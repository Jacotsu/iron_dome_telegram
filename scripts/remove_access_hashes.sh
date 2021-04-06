#!/usr/bin/env bash
sed '/^.*"access_hash":.*$/d' "$@"
