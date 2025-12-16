#!/bin/bash
# Test runner wrapper for mutmut
cd /home/ssm-user/Fall-25-CS-5300/active_interview_backend
exec python3 manage.py test "$@" --verbosity=0 --failfast 2>/dev/null
