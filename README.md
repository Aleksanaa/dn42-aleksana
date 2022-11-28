# My DN42 config and scripts (WIP)

I use github workflow to generate wireguard and bird config files, and set cron to run bash scripts on nodes to fetch artifacts once in a while. This repo is inspired by DN42 official registry repo.

## Peer with me

The peer config file is designed to be as simple as possible. Below is a valid config file which defines two peers with my Los Angeles and Montreal node:

```ini
[shared]
asn = 4242422562

[lax]
address = las.innocent.neko.com
pubkey = VRNde3NgskHROo/edwed7y6gdeMskSM/GY/yOqdewde=

[mtl]
address = nyc.innocent.neko.com
pubkey = qWEsh2/4dewejmVrywDcd/oiwwlUzuHsWId3e+awklN=
```

Begin with a common practice. To peer with a node with link-local address (then you'd better have `extended next hop on`), you can set:

```ini
# config/peers/<your nickname>.conf

[lax]
asn = <your asn number, dn42 or neonetwork>
link_local = <your link local address>
address = <domain or ip of your node on internet>
port = <port you set for wireguard connection with me>
pubkey = <your wireguard public key>
pskey = <your wireguard preshared key>
```

And the rules:

1. do not write any abbreviation of subnet mask like `/32` or `/64` in config file. And do not cover your value by single or double quotes. Please also check `config/nodes` for node names, address (endpoint) and ipv4/ipv6 availability in advance.

2. Nickname is the filename of the config file, and it should be no less than 4 characters and no more than 10 characters, containing only numbers, lowercase English letters and half-width underscore. It's better to pick your popular nickname which is used in such as Telegram, Github or Discord account so the name of interface and bird protocols are more recognizable.

3. The name of the section should be the name of the node I have.

4. If the link-local address is `fe80::<your asn last 4 digits, removing left '0'>`, you can skip it. (for example, fe80::365 for 4242420365 and fe80::2717 for 4242422717)

5. Since both of us can take the initiative to establish the wireguard tunnel, the address is not necessary if my node has one. Do not provide ipv6 address, or domain that only have AAAA record to my nodes that do not have ipv6 access, and same for ipv4.

6. If the port you provide is `2<my asn last 4 digits>`, in this case `20365`, you can skip it as well. If you do not want to provide an address, the port should also be ignored.

7. The preshared key is not recommended to use because it is meant to be private. However, if you still want to include it for some reasons, you can still write it there.

This is another example, which peers with DN42 address instead of link-local one.

```ini
# config/peers/<your nickname>.conf

[lax]
asn = <your asn number, dn42 or neonetwork>
ipv4 = <dn42 ipv4 address of your node>
ipv6 = <dn42 ipv6 address of your node>
address = <domain or ip of your node on internet>
port = <port you set for wireguard connection with me>
pubkey = <your wireguard public key>
pskey = <your wireguard preshared key>
```

The ipv4 and ipv6 addresses are also not both necessary. If you only set one address, the script will set up peer with that address only, thus only ipv4 or ipv6 BGP tables are given.

If you want to peer with multiple nodes of mine, you can add a section named `[shared]`, and place anything in common there. Note that `[shared]` has lower priority than other node sections. If you want to undefine the keys defined in `[shared]`, you can write `<key> = none`.

Play with it!