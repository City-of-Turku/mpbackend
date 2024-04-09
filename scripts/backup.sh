# NOTE, this script is added to the crontab as: 1 0 * * * /home/azureuser/mpbackend/scripts/backup.sh

#!/bin/bash
BACKUP_PATH=/home/azureuser/backups/
current_date=$(date +"%Y-%m-%d")
echo "Backuping mobilityprofile database on current date $current_date..."
docker exec -i mpbackend_postgres_1 /usr/bin/pg_dump -U mobilityprofile -F t mobilityprofile | gzip -9 > ${BACKUP_PATH}mpbackend_backup_${current_date}.tar.gz
echo "Backup finished."

: 'To restore:
To inspect the container:
docker inspect mpbackend_postgres_1

1. Go to the directory defined in constant $BACKUP_PATH, where the backups are located
2. Unzip the .gz file, e.g.: gunzip mpbackend_backup_YYYY-MM-DD.tar.gz
2. copy the .tar file to the container: e.g.: docker cp mpbackend_backup_YYYY-MM-DD.tar mpbackend_postgres_1:/tmp
3. Restore the database: docker exec mpbackend_postgres_1 pg_restore -U mobilityprofile -c -d mobilityprofile /tmp/mpbackend_backup_YYYY-MM-DD.tar
4. Optionally, remove the backup file from the container: docker exec mpbackend_postgres_1 rm /tmp/mpbackend_backup_YYYY-MM-DD.tar

# For additional informaition, e.g.: https://simplebackups.com/blog/docker-postgres-backup-restore-guide-with-examples/#back-up-a-docker-postgresql-database
'
