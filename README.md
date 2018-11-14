# Hass.io Dropbox Uploader

This Hass.io add-on provides a simple way to upload your snapshots to Dropbox.

## Installation

Add this repository URL in Hass.io:

	https://github.com/d0ugal/hassio-dropbox-upload


## Configuration

### Dropbox

You will need to create a [Dropbox app](https://www.dropbox.com/developers/apps)

1. Choose `Dropbox API`
2. Either type of Dropbox app should work (Full or App directory)
3. Give it a unique name, this can be anything
4. Click `Generate` under "Generated access token" and copy the token.


### All Configuration Options


| Options              	| Default       	| Description                                                                                                                      	|
|----------------------	|---------------	|----------------------------------------------------------------------------------------------------------------------------------	|
| access_token         	|               	| Dropbox API Access Token. Required.                                                                                              	|
| dropbox_dir          	| "/snapshots"  	| The directory name in dropbox to upload snapshots.  Must start with a forward slash.                                             	|
| keep                 	| 10            	| The number of snapshots to keep. Once the limit is reached,  older snapshots will be removed from Hass.io and Dropbox.           	|
| mins_between_backups 	| 60            	| How often, in minutes, should the addon check for new backups.                                                                   	|
| filename             	| snapshot_slug 	| What filename strategy should be used in Dropbox? Can be either  "snapshot_name" or "snapshot_slug".                             	|
| debug                	| false         	| A flag to enable/disable verbose logging. If you are  having issues, change this to True and include the output  in bug reports. 	|


### Full Configuration Example

```
{
  "access_token": "<YOUR_ACCESS_TOKEN>",
  "dropbox_dir": "/snapshots",
  "keep": 10,
  "mins_between_backups": 60,
  "filename": "snapshot_name",
  "debug": false
}
```

## Automation

Here is the automation I use to create a snapshot and upload it to Dropbox.

```
  - alias: Backup Nightly
    trigger:
      platform: time
      at: '02:00:00'
    action:
      - service: hassio.snapshot_full
        data_template:
          name: Automated Backup {{ now().strftime('%Y-%m-%d') }}
          password: !secret snapshot_password
```


## Questions/Ideas

This project is young, and very light. I am interested in adding some features -
so long as it remains simple and easy to use. Please let me know of your ideas
and feedback!
