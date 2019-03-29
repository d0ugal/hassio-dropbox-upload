Dropbox_Upload 1.1.4 (2019-03-29)
=================================

- Fixed an issue with the 1.1.3 release. The version hadn't been updated.


Dropbox_Upload 1.1.3 (2019-03-29)
=================================

Bugfixes
--------

- Lock in the supported architectures (#53)


Dropbox_Upload 1.1.2 (2018-12-30)
=================================

Bugfixes
--------

- Fix errors when uploading to DropBox  (#43)


Dropbox_Upload 1.1.1 (2018-11-14)
=================================

Bugfixes
--------

- Default to "snapshot_slug" so we don't switch over all users as they upgrade (#37)


Dropbox_Upload 1.1.0 (2018-11-14)
=================================

Features
--------

- Add a new "filename" setting to customise the filenames saved in dropbox (#15)
- The dropbox_dir is now validated to ensure it isn't an empty string. (#16)
- Add a warning if snapshots are not "protected", adding a password is always a good idea (#31)
