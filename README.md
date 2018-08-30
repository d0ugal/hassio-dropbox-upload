# Hass.io Dropbox Uploader

This Hass.io add-on provides a simple way to upload your snapshots to Dropbox.

## Installation

Add this repository URL in Hass.io:

	https://github.com/d0ugal/hassio-dropbox-upload


## Configuration

You will need to create a [Dropbox app](https://www.dropbox.com/developers/apps)

1. Choose `Dropbox API`
2. Then `Full Dropbox` 
   (See [#1](https://github.com/d0ugal/hassio-dropbox-upload/issues/1))
3. Give it a unique name, this can be anything
4. Click `Generate` under "Generated access token" and copy the token.

After that, the config is simple. You just need to specify the access token and 
a directory name.

```
{
  "access_token": "ACCESS TOKEN",
  "dropbox_dir": "/hass-snapshots/"
}
```


## Questions/Ideas

This project is young, and very light. I am interested in adding some features -
so long as it remains simple and easy to use. Please let me know of your ideas 
and feedback!
