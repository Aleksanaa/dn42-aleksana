#!/bin/bash

private_key_head="MC4CAQAwBQYDK2VuBCIEIA=="
public_key_head="MCowBQYDK2VuAyEA"

b64join() {
  echo -e "$(printf ${1} \
    | base64 -d \
    | sed -e 's/\x0/whatsup/g')$(printf ${2} \
    | base64 -d \
    | sed -e 's/\x0/whatsup/g')" \
  | sed -e "s/whatsup/\x0/g"
}

genkey() {
    openssl genpkey -algorithm X25519 -outform der \
    | tail -c 32 | base64
}

pubkey() {
    b64join ${private_key_head} ${1} \
    | openssl pkey -inform DER -outform DER -pubout \
    | tail -c 32 | base64
}

exchange_key() {
    openssl pkeyutl -derive \
      -keyform DER -inkey <(b64join ${private_head} ${1}) \
      -peerform DER -peerkey <(b64join ${public_head} ${2} | sed 's/K$/=/') \
    | base64
}

decrypt_file() {
    openssl aes-256-cbc -d -a -k ${1} -in ${1} -out ${2}
}