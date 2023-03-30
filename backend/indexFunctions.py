import openai
import pinecone
import dateutil
import dotenv
import os
import datetime
import json
from datetime import datetime

from calendarFunctions import Calendar

class Index:
    cal = None
    vector_store=None
    event_ids_by_date = {}

    def __init__(self,token_file_path):
       
        #Get the pinecone api key from the .env file
        dotenv.load_dotenv()
        #supply Pinecone API key
        pinecone.init(api_key=os.getenv("PINECONE_API_KEY"),environment="us-central1-gcp")

        #Create a pinecone index or use an existing one if the index already exists
        index_name = "events-vector-store"
        
        #check if index exists
        if index_name in pinecone.list_indexes():
            self.vector_store = pinecone.Index(index_name)
        else:
            self.vector_store = pinecone.create_index(name=index_name, dimension = 1536)
        
        #Instantiate the calendar object
        self.cal=Calendar(token_file_path)

        #Get the list of events from the calendar
        events = self.cal.get_all_events()

        #Create a vector store
        self.create_vector_store(events)

        return
    
    def create_vector_store(self, events):
            # Prepare data for the vector store
        data = {}
        for event in events:
            event_id = event['id']
            event_date_str = event['start']['dateTime']
            event_date_datetime = datetime.fromisoformat(event_date_str)
            event_date = event_date_datetime.strftime('%Y-%m-%d')


            # Generate event string and create the embedding
            event_string = str(self.parse_event(event))
            event_embedding = Index.get_embedding(event_string)

            if event_date not in data:
                data[event_date] = {
                    'event_ids': [],
                    'values': []
                }

            data[event_date]['event_ids'].append(event_id)
            data[event_date]['values'].append(event_embedding)


        data = {'vectors':[data]}
        vectors = data['vectors']
        #Write data to a json file
        with open('data.json', 'w') as outfile:
            json.dump(data, outfile)
        
        # Upsert the vectors into the Pinecone index
        self.vector_store.upsert(vectors)
               


    @staticmethod
    def get_embedding(text,model="text-embedding-ada-002"):
        text = text.replace("\n"," ")
        #add the openai api key from the .env file
        dotenv.load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        return openai.Embedding.create(input=text, model=model)['data'][0]
    
    def parse_event(self,event):
        event_string = ''

        # Get the summary (name/title) of the event
        summary = event.get('summary', '')
        if summary:
            event_string += f'Summary: {summary} '

        # Get the location of the event
        location = event.get('location', '')
        if location:
            event_string += f'Location: {location} '

        # Get the description of the event
        description = event.get('description', '')
        if description:
            event_string += f'Description: {description} '

        # Get the list of attendees for the event
        attendees = event.get('attendees', [])
        if attendees:
            attendee_emails = [attendee.get('email', '') for attendee in attendees]
            event_string += f'Attendees: {", ".join(attendee_emails)} '

        # Return the event string
        return event_string

    #Returns a list of the ids and their scores mathcing the query. The top 5 results are returned.
    def query_index(self,query_text, event_ids=None):
        # Get the embedding of the query text using the same model as before
        query_embedding = self.get_embedding(query_text)
        # Query the index for the closest event to the query text
        results = self.vector_store.query(query_embedding['embedding'], top_k=len(event_ids) if event_ids else 5)
        # Get the event ID and metadata from the query results
        if event_ids:
            id_score_list = [
                (match['id'], match['score'])
                for match in results['matches']
                if match['id'] in event_ids
            ]
        else:
            id_score_list = [(match['id'], match['score']) for match in results['matches']]

        return id_score_list
    
    def delete_all_vectors(self):
        #load the pinecone api key from the .env file
        dotenv.load_dotenv()
        self.vector_store.delete(deleteAll=True)

test = Index('backend/creds/token.json')
