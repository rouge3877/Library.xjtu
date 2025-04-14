#!/bin/bash

No=$1
kid="P003"
sp="eastnorthda"



BASE_URL="http://202.117.24.3:8088/seatuieast/#"
STATUS_URL="http://202.117.24.3:8088/quserinfo?cardno=$No"

check_status() {
    resp=$(curl -s "$STATUS_URL")
    status=$(echo "$resp" | jq '.status')
    cu=$(echo "$resp" | jq -r '.cu')
    msg=$(echo "$resp" | jq -r '.message')

    if [[ "$status" == "1" ]]; then
        if [[ "$cu" != "$No" ]]; then
            echo "Occupied by others"
            return
        fi
        if echo "$msg" | grep -q "$kid"; then
            echo "Already reserved"
            return
        fi
    fi
    echo "Available"
}

initialize() {
    page=$(curl -s "$BASE_URL")
    echo "$page" | grep -q "<h2>" || {
        echo "Missing critical page element"
        exit 3
    }
}

submit() {
    status=$(check_status)

    if [[ "$status" != "Available" ]]; then
        echo "$status"
        exit 4
    fi

    result=$(curl -s -X POST -d "No=$No&kid=$kid&sp=$sp" "$BASE_URL")
    content=$(echo "$result" | pup 'span text{}' | head -n 1)

    if echo "$content" | grep -q "P003" && echo "$content" | grep -q "成功"; then
        echo "Reservation success"
        exit 0
    elif echo "$content" | grep -q "已被预约"; then
        echo "Seat taken"
        exit 5
    else
        echo "Unknown response"
        exit 2
    fi
}

# 主程序
# initialize
submit

