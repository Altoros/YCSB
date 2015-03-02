## Fedora/Red Hat bug: https://bugzilla.redhat.com/show_bug.cgi?id=1020147
#!/bin/sh
sed -i "s|Defaults    requiretty|#Defaults    requiretty|g" /etc/sudoers

