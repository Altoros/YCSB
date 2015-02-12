# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi

# User specific environment and startup programs

export JAVA_HOME=/usr/java/default

PATH=$JAVA_HOME/bin:$PATH:$HOME/bin

export PATH

