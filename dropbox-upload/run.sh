#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Dropbox Upload script..."
exec python3 -m dropbox_upload
