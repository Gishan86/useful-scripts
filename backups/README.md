# Backups
Here are some scripts I personally use to create backups of stuff that is important to me.
Once again these are tailored to my needs, but can easily be adopted to what you are trying to do.

Here is an overview:

 - [Email Backup](#email-backup)

## Email Backup
Although I trust the email provider I'm with, I don't want to rely solely on their infrastructure and backup solution.
And so I wrote this script which simply logs in to my mail provider, gets all mails in all folders and writes them as EML files on my disk.

[Link](backup_emails.py)

### Requirements
 - Python 3
 - Keyring (23.13.1)

### Usage
```
> python backup_emails.py -s <HOST> -u <USER> -p <PWD> -l <OUTPUT-DIR>
```

### Options
```
 -h, --help			Help for all options
 -s, --server HOST 		Server url of your mail provider
 -u, --username USER		Username for logging into your mail account
 -p, --password PWD		Password for logging into your mail account
 -l, --localfolder FOLDER	Local folder where EML files should be written
 -o, --overwrite		Overwrite already downloaded mails (default: False)
 -c, --credentials		Save user and password in the OS keyring (default: False)
 -v, --verbose			Verbose output for debugging (default: False)
```

### Example
```
> python backup_emails.py -s imap://mails.org -u user@mails.org -p mypassword -l "c:\\users\\dev\\desktop\\backup\\"
```