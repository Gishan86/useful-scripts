import imaplib
import argparse
import re
import os
import json
import hashlib
import keyring
import logging

KR_NAMESPACE = "mailbackup"
KR_ENTRY_HOST = "HOST"
KR_ENTRY_USER = "USER"
KR_ENTRY_PWD = "PWD"

def init_args():
    #init variables
    host = ""
    username = ""
    password = ""
    local_folder = ""
    overwrite = False
    interactive = False
    save_keyring = False

    #load values from keyring
    host = keyring.get_password(KR_NAMESPACE, KR_ENTRY_HOST)
    username = keyring.get_password(KR_NAMESPACE, KR_ENTRY_USER)
    password = keyring.get_password(KR_NAMESPACE, KR_ENTRY_PWD)

    #parse arguments
    argparser = argparse.ArgumentParser(description="Dump a IMAP folder into .eml files")
    argparser.add_argument("-s", "--server", dest="host", help="IMAP host, like imap.gmail.com", default="", required=True)
    argparser.add_argument("-u", "--username", dest="username", help="IMAP username", default="", required=True)
    argparser.add_argument("-p", "--password", dest="password", help="IMAP password", default="", required=True)
    argparser.add_argument("-l", "--localfolder", dest="local_folder", help="Local folder where to save .eml files", default="data")
    argparser.add_argument("-o", "--overwrite", dest="overwrite", help="Overwrite already downloaded files", action=argparse.BooleanOptionalAction, default=False)
    argparser.add_argument("-c", "--credentials", dest="save_credentials", help="Save user and password", action=argparse.BooleanOptionalAction, default=False)
    argparser.add_argument("-v", "--verbose", dest="verbose", help="Verbose output for debugging", action=argparse.BooleanOptionalAction, default=False)
    args = argparser.parse_args()

    #credential arguments (take only if present)
    if not args.host == "":
        host = args.host

    if not args.username == "":
        username = args.username
    
    if not args.password == "":
        password = args.password
    
    local_folder = args.local_folder
    overwrite = bool(args.overwrite)
    interactive = bool(args.interactive)
    save_keyring = bool(args.save_credentials)
    verbose = bool(args.verbose)

    if not host:
        host = input("Host: ")
    
    if not username:
        username = input("User: ")
    
    if not password:
        password = input("Password: ")

    return host, username, password, local_folder, overwrite, interactive, save_keyring, verbose

def save_credentials(host : str, username : str, password : str, save_keyring: bool):
    if save_keyring == False:
        logging.debug("Not saving credentials to keyring.\n" %(host, username))
        return
    
    keyring.set_password(KR_NAMESPACE, KR_ENTRY_HOST, host)
    keyring.set_password(KR_NAMESPACE, KR_ENTRY_USER, username)
    keyring.set_password(KR_NAMESPACE, KR_ENTRY_PWD, password)
    logging.debug("Credentials saved to keyring.\n" %(host, username))

def read_downloaded(local_folder):
    filepath = "%s/.downloaded" %(local_folder)

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)

    return {}

def write_downloaded(local_folder, downloaded : dict):
    filepath = "%s/.downloaded" %(local_folder)

    with open(filepath, "w") as f:
        json.dump(downloaded, f)

def connect(host, username, password):
    mailbox = imaplib.IMAP4_SSL(host)
    mailbox.login(username, password)

    logging.debug("Logged in to %s as %s.\n" %(host, username))
    return mailbox

def disconnect(mailbox : imaplib.IMAP4_SSL):
    #mailbox.close() not needed for this usecase
    mailbox.logout()
    logging.debug("Logged out from mailbox.\n")

def get_imap_folders(host, username, password):
    mailbox = connect(host, username, password)

    response = mailbox.list()[1]
    folders = []
    for r in sorted(response):
        folder = r.decode()
        folder = re.sub(r"(?i)\(.*\)", "", folder, flags=re.DOTALL)
        folder = re.sub(r"(?i)\".\"", "", folder, flags=re.DOTALL)
        folder = re.sub(r"(?i)\"", "", folder, flags=re.DOTALL)
        folder = folder.strip()
        folders.append(folder)
    
    disconnect(mailbox)
    return folders

def get_filepath(local_folder, folder, filehash):
    return "%s/%s/%s.eml" %(local_folder, folder, filehash)

def archive_mails(local_folder, folder, downloaded, overwrite, host, username, password):
    try:
        #connect to IMAP server
        mailbox = connect(host, username, password)

        #create output folder
        filepath = "%s/%s" %(local_folder, folder)
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        #get mails
        mailbox.select(folder, readonly=True)
        data = mailbox.search(None, "ALL")[1]
        nums = data[0].split()

        logging.info("Archiving %s...%i\n" %(folder, len(nums)))
        done = downloaded[folder]

        #write eml files
        for num in nums:

            if not overwrite and (int(num) < int(done)):
                continue

            responseMail = mailbox.fetch(num, "(RFC822)")[1]
            for response_part in responseMail:
                if isinstance(response_part, tuple):
                    mBytes = response_part[1]

                    #get filepath for mail
                    filehash = hashlib.md5(mBytes).hexdigest()
                    filepath = get_filepath(local_folder, folder, filehash)

                    #skip if file exists and overwrite is not active
                    if not overwrite and os.path.isfile(filepath):
                        continue

                    #write file
                    with open(filepath, "wb") as f:
                        logging.debug("Writing file %s...\n" %(filepath))
                        f.write(mBytes) #mStr.encode("utf-8"))
                    
                    #remember mail number
                    downloaded[folder] = int(num)

                #write downloaded
                write_downloaded(local_folder, downloaded)
        
        #write downloaded when folder is complete
        write_downloaded(local_folder, downloaded)

    except Exception as e:
        logging.error("Error %s\n" %(e))

    finally:
        #write downloaded at the end
        write_downloaded(local_folder, downloaded)

        #disconnect from IMAP server
        disconnect(mailbox)

def main():
    #init variables
    host, username, password, local_folder, overwrite, save_keyring, verbose = init_args()

    #init logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    #save credentials
    save_credentials(host, username, password, save_keyring)

    #get already downloaded
    downloaded = read_downloaded(local_folder)

    #get folders
    folders = get_imap_folders(host, username, password)

    #archive mails
    for folder in folders:
        archive_mails(local_folder, folder, downloaded, overwrite, host, username, password)

if __name__ == "__main__":
    main()