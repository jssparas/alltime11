# run a celerybeat :)
celery -A alltime11 beat --loglevel=debug  --logfile=/var/log/celerybeat.log --detach

# Wait for Celery Beat to finish
wait $!

# Clean up on container exit
cleanup() {
    rm -f ./celerybeat.pid
}

# Register cleanup function to be called on SIGTERM
trap 'cleanup' SIGTERM

# Wait for the trap signal indefinitely
while true; do
    sleep 1 &
    wait $!
done