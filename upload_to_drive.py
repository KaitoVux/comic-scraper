import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_credentials():
    """Gets valid user credentials from storage or creates new ones."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def create_folder(service, folder_name, parent_id=None):
    """Creates a folder in Google Drive and returns its ID."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

def upload_file(service, file_path, folder_id=None):
    """Uploads a file to Google Drive."""
    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata,
                                media_body=media,
                                fields='id').execute()
    return file.get('id')

def main():
    # Get credentials
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    # Create main folder for the novel
    main_folder_name = 'Mục Thần Ký'
    main_folder_id = create_folder(service, main_folder_name)
    
    # Create subfolders
    txt_folder_id = create_folder(service, 'txt_files', main_folder_id)
    json_folder_id = create_folder(service, 'json_files', main_folder_id)
    
    # Upload TXT files
    txt_dir = 'output/mục_thần_ký_txt'
    for filename in os.listdir(txt_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(txt_dir, filename)
            print(f'Uploading {filename}...')
            upload_file(service, file_path, txt_folder_id)
    
    # Upload JSON files
    json_dir = 'output'
    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(json_dir, filename)
            print(f'Uploading {filename}...')
            upload_file(service, file_path, json_folder_id)
    
    print('Upload complete!')

if __name__ == '__main__':
    main() 