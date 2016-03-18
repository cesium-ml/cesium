#!/bin/bash

retry () {
    # https://gist.github.com/fungusakafungus/1026804
    local retry_max=3
    local count=$retry_max
    while [ $count -gt 0 ]; do
        "$@" && break
        count=$(($count - 1))
        sleep 1
    done

    [ $count -eq 0 ] && {
        echo "Retry failed [$retry_max]: $@" >&2
        return 1
    }
    return 0
}

section () {
    echo -en "travis_fold:start:$1\r"
    .drone/header.py $1
}

section_end () {
    echo -en "travis_fold:end:$1\r"
}

export -f retry
export -f section
export -f section_end
