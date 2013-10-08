#!/bin/bash

#why am I scripting to my script?  nonetheless in bash...
#if [[ -z $1 ]]
#then
#    echo "You need to supply the sample directory as the first argument"
#    exit
#fi
debug=true
package=org.kivy.twitter
name="Twitter Example"
dir=~/projects/twitter/src/
version=0.1
orientation='portrait'

#jars in lib/  be sure to copy to pfa
#jars=("libs/twitter4j-core-3.0.3.jar" "libs/twitter4j-async-3.0.3.jar")
jars=()
jar_options=()
for j in "${jars[@]}"
do
    jar_options+=(--add-jar "$j")
done

perms=('INTERNET' 'ACCESS_NETWORK_STATE')
perm_options=()
for p in "${perms[@]}"
do
    perm_options+=(--permission "$p")
done

if $debug
then
    mode=('debug' 'installd')
else
    mode=('release')
fi

command=(./build.py --package "$package" --version $version --orientation "$orientation" --name "$name" --dir "$dir")
#command+=("${jar_options[@]}" "${perm_options[@]}" "${mode[@]}")
command+=("${perm_options[@]}" "${mode[@]}")

#echo "${command[@]}"
"${command[@]}"
