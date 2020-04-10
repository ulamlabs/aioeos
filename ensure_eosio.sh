#!/bin/bash
x=0
while true;
do
    docker ps | grep -q eos-testnet > /dev/null
    if [ $? -eq 0 ]; then
        y=0
        while [ $y -lt 10 ];
        do	
            docker exec eos-testnet cleos get table eosio eosio delband &> /dev/null
            if [ $? -eq 0 ]; then
                echo "EOS bootstrapped ($y retries, $x reboots)"
                exit 0
            fi
            ((y+=1))
            sleep 10
        done
        echo Retry limit exceeded, rebooting
    fi
    ((x+=1))
    docker-compose stop eos-testnet &> /dev/null
    docker-compose rm -f &> /dev/null
    docker-compose up -d eos-testnet &> /dev/null
    sleep 5
done
