# -*- coding: utf-8 -*-
class Attendance(object):
    def __init__(self, user_id, timestamp, status):
        self.user_id = user_id
        self.timestamp = timestamp
        self.status = status

    def __str__(self):
        return 'userid> {}'.format(self.user_id) + ' / ' 'timestamp> {}'.format(
            self.timestamp) + ' / ' 'status> {}'.format(self.status)

    def __repr__(self):
        return 'userid> {}'.format(self.user_id) + ' / ' 'timestamp> {}'.format(
            self.timestamp) + ' / ' 'status> {}'.format(self.status)