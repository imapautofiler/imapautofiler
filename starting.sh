#!/usr/bin/env bash

if [ "$1" == "bash" ] || [ "$1" == "sh" ]; then
    exec "${@}"
fi



# Check if the target is not a directory
if [ ! -d "/app/config.d/" ]; then
  echo "Folder \"/app/config.d/\" is missing !"
  echo "Please mount your config into this folder"
  exit 1
fi


command=( "imapautofiler" )

if [ -n "$DEBUG" ] && [ "$DEBUG" == "true" ]; then
  command+=( "--debug" )
fi

if [ -n "$VERBOSE" ] && [ "$VERBOSE" == "true" ]; then
  command+=( "--verbose" )
fi

if [ -n "$LISTMAILBOXES" ] && [ "$LISTMAILBOXES" == "true" ]; then
  command+=( "--list-mailboxes" )
fi

if [ -n "$DRYRUN" ] && [ "$DRYRUN" == "true" ]; then
  command+=( "--dry-run" )
fi

for f in "/app/config.d"/*; do
  if [ -f "$f" ]; then
    echo "## STARTING MAILBOX $f "
    
    if [ -n "$VERBOSE" ] && [ "$VERBOSE" == "true" ]; then
      echo "Command used to start : ${command[@]}"
    fi

    "${command[@]}" -c "$f"
    echo ""
  fi
done

