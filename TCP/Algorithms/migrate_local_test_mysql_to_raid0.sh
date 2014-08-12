#!/bin/sh

#This migrates the test-version setup'd mysql table files from local disk to
#transx RAID0 disk.

# NOTE: the  ned_feat_cache tables MUST BE NEWLY created if we wish to
#       uncomment the ned_feat_cache tables bit & move it to raid0
#       - otherwise a sym-link to nothing will be move to raid0 & tables lost!

sudo mysqladmin shutdown
sudo rm -Rf /media/raid_0/object_test_db
sudo rm -Rf /media/raid_0/source_test_db
#sudo rm -Rf /media/raid_0/ned_feat_cache
sudo mv /var/lib/mysql/object_test_db /media/raid_0/
sudo mv /var/lib/mysql/source_test_db /media/raid_0/
#sudo mv /var/lib/mysql/ned_feat_cache /media/raid_0/
sudo ln -s /media/raid_0/object_test_db /var/lib/mysql/object_test_db
sudo ln -s /media/raid_0/source_test_db /var/lib/mysql/source_test_db
#sudo ln -s /media/raid_0/ned_feat_cache /var/lib/mysql/ned_feat_cache
sudo chown -R mysql /media/raid_0/object_test_db
sudo chown -R mysql /media/raid_0/source_test_db
#sudo chown -R mysql /media/raid_0/ned_feat_cache
sudo /usr/local/bin/mysqld_safe --binlog-ignore-db=minor_planet --binlog-ignore-db=source_test_db --binlog-ignore-db=object_test_db --binlog-ignore-db=source_db --binlog-ignore-db=object_db &
