#!/bin/bash

OPTSPEC=":hu:p:t:f:"

show_help() {
cat << EOF
Usage: $0 [-u USER] [-p PASSWORD] [-f FROM_FOLDER] [-t TARGET_HOST]
Script to export grafana dashboards
    -u      Required. cClear user to login
    -p      Required. cClear user password to login
    -t      Required. The IP of the source cClear host i.e 10.51.10.32
    -f      Optional. The name of the folder to export from, double quotes with spaces. Export all folders if not
    specified.
    -h      Display this help and exit.
EOF
}

###### Check script invocation options ######
while getopts "$OPTSPEC" optchar; do
    case "$optchar" in
        h)
            show_help
            exit
            ;;
        u)
            USER="$OPTARG";;
        p)
            PASSWORD="$OPTARG";;
        t)
            HOST="$OPTARG";;
        f)
            FROM="$OPTARG";;
        \?)
          echo "Invalid option: -$OPTARG" >&2
          exit 1
          ;;
        :)
          echo "Option -$OPTARG requires an argument." >&2
          exit 1
          ;;
    esac
done

if [ -z "$USER" ] || [ -z "$PASSWORD" ] || [ -z "$HOST" ]; then
    show_help
    exit 1
fi

# set some colors for status OK, FAIL and titles
SETCOLOR_SUCCESS="echo -en \\033[0;32m"
SETCOLOR_FAILURE="echo -en \\033[1;31m"
SETCOLOR_NORMAL="echo -en \\033[0;39m"
SETCOLOR_TITLE_PURPLE="echo -en \\033[0;35m" # purple 

# usage log "string to log" "color option"
function log_success() {
   if [ $# -lt 1 ]; then
       ${SETCOLOR_FAILURE}
       echo "Not enough arguments for log function! Expecting 1 argument got $#"
       exit 1
   fi

   timestamp=$(date "+%Y-%m-%d %H:%M:%S %Z")

   ${SETCOLOR_SUCCESS}
   printf "[${timestamp}] $1\n"
   ${SETCOLOR_NORMAL}
}

function log_failure() {
   if [ $# -lt 1 ]; then
       ${SETCOLOR_FAILURE}
       echo "Not enough arguments for log function! Expecting 1 argument got $#"
       exit 1
   fi

   timestamp=$(date "+%Y-%m-%d %H:%M:%S %Z")

   ${SETCOLOR_FAILURE}
   printf "[${timestamp}] $1\n"
   ${SETCOLOR_NORMAL}
}

function log_title() {
   if [ $# -lt 1 ]; then
       ${SETCOLOR_FAILURE}
       log_failure "Not enough arguments for log function! Expecting 1 argument got $#"
       exit 1
   fi

   ${SETCOLOR_TITLE_PURPLE}
   printf "|-------------------------------------------------------------------------|\n"
   printf "|$1|\n";
   printf "|-------------------------------------------------------------------------|\n"
   ${SETCOLOR_NORMAL}
}

counter=0

function init() {
   DATE_TIME=$(date '+%d%m%Y_%H%M%S')
   DASH_DIR="$PWD/dashboards_${HOST}_${DATE_TIME}"
   if [ ! -d "${DASH_DIR}" ]; then
   	 mkdir "${DASH_DIR}" 
   else
   	 log_title "----------------- A $DASH_DIR directory already exists! -----------------"
   fi
}

init

# host url
if [[ ! "$HOST" == "https://"* ]]; then
  HOST="https://$USER:$PASSWORD@$HOST"
fi

folder_json=$(curl --noproxy '*' -k --request "GET" -H "Content-Type:application/json" "$HOST/graph-engine/api/folders")
# From folder specified:
if [ ${#FROM} -gt 0 ]; then
   # Find matching folder from remote (with folder title)
  IFS=";" read -a arrFROM <<< ""$FROM""
  FOLDER_UID=()
    for fr in "${arrFROM[@]}"
    do
        echo "folder: $fr"
        echo "1"
        FOLDER_UID+=($(echo $folder_json | jq -r '.[] | select(.title == "'"$fr"'") | .uid'))
    done
  
  #FOLDER_UID=$(echo $folder_json | jq -r '.[] | select(.title == "'"$FROM"'") | .uid')
  # Folder found: get the collection of dashboard uids in this folder
  dashboard_uids=""
  for fuid in "${FOLDER_UID[@]}"
  do
    uid=$(echo "$fuid" | xargs)
    echo "fuid: $uid"
  # Folder not found, prompt error and get out
    if [ -z "$fuid" ] ; then
      log_failure "Folder $fuid is not found. Please check spelling and double quote with any spaces."
      exit 1
    fi
    dashboard_uids="$dashboard_uids $(curl --noproxy '*' -k "$HOST"/graph-engine/api/search\?query\=\& | \
    jq -r '.[] | select(.type | contains("dash-db")) | select(.folderUid != null) | select(.folderUid == "'"$uid"'") | .uid')"
  done
  
# From all folders:
else
  dashboard_uids=$(curl --noproxy '*' -k "$HOST"/graph-engine/api/search\?query\=\& | \
  jq -r '.[] | select(.type | contains("dash-db")) | .uid')
fi

 # treestate
 if [[ ! -e "$DASH_DIR/treestate.ts" ]]; then
    printf  "import { NodeData } from 'react-folder-tree';\nexport const dashboardTree: NodeData =\
    {\n name: 'cPacket Dashboards',\n dashPath: 'assets/dashboards',\n children: [\n" > \
    "$DASH_DIR/treestate.ts"
 fi
 arrFolders=()
# Export dashboards
for dashboard_uid in $dashboard_uids; do
   url=$(echo "$HOST/graph-engine/api/dashboards/uid/$dashboard_uid" | tr -d '\r')
   dashboard_json=$(curl --noproxy '*' -k "$url")
   dashboard_title=$(echo "$dashboard_json" | jq -r '.dashboard | .title')
   dashboard_file=$(echo "$dashboard_title" | sed -r 's/[ \/]+/_/g' | sed -r 's/[-\/]+/_/g' | tr '[:upper:]' '[:lower:]')
   dashboard_folder_raw=$(echo "$dashboard_json" | jq -r '.meta | .folderTitle')
   dashboard_folder=$(echo "$dashboard_json" | jq -r '.meta | .folderTitle' | sed -r 's/[ \/]+/_/g' | sed -r 's/[-\/]+/_/g')
   dashboard_folderId=$(echo "$dashboard_json" | jq -r '.meta | .folderId')

   folder_path=$(echo ${dashboard_folder} | tr '[:upper:]' '[:lower:]')
   # create the folder if not existing
   if [ ! -d "${DASH_DIR}/${folder_path}" ]; then
   	 mkdir "${DASH_DIR}/${folder_path}"
     arrFolders+=(${folder_path})
   fi
    # treestate
    if [[ ! -e "$DASH_DIR/${folder_path}/treestate.ts" ]]; then
        printf  "{ name: '${dashboard_folder_raw}',\n dashPath: '${folder_path}',\n children: [\n" > \
        "$DASH_DIR/${folder_path}/treestate.ts"
    fi
   
   counter=$((counter + 1))
   printf "{ name: '${dashboard_title}', dashPath: '${dashboard_file}.json' },\n" >> "$DASH_DIR/${folder_path}/treestate.ts"
   # save dashboard with meta, dashboard and folder.
   echo "$dashboard_json" | jq  '.dashboard | . += {"id":null, "folderTitle": "'"$dashboard_folder_raw"'"}' > \
   "$DASH_DIR/${folder_path}/${dashboard_file}.json"
   log_success "Dashboard has been saved\t\t title=\"${dashboard_file}\", uid=\"${dashboard_uid}\",
   path=\"${DASH_DIR}/${folder_path}/${dashboard_file}.json\"."
done

for value in "${arrFolders[@]}"
do
    cat "$DASH_DIR/${value}/treestate.ts" >> "$DASH_DIR/treestate.ts"
    printf "],\n},\n" >> "$DASH_DIR/treestate.ts"
done
printf "],\n};\n" >> "$DASH_DIR/treestate.ts"

log_title "${counter} dashboards were saved in ${DASH_DIR}";
log_title "------------------------------ FINISHED ---------------------------------";
