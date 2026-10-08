# Editors (site administrators)

rely_on_username: true

<!--
HOW THIS FILE WORKS
- One Wikimedia account per line, e.g. `- Yug`.
- rely_on_username: true   -> usernames are enough. The site looks up each account's user id on Commons
                              (api.php?action=query&list=users&ususers=A|B) and compares it with the id of the
                              account that logged in. Renamed accounts must be updated here.
- rely_on_username: false  -> strict mode: write `Username | id`; lines without an id grant nothing.
- Lines starting with # are ignored.
-->

- Yug
- Jesedmateo
