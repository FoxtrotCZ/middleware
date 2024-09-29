from bases.FrameworkServices.SimpleService import SimpleService

from middlewared.utils.disks import get_disks_with_identifiers
from middlewared.utils.disk_stats import get_disk_stats


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.last_stats = {}
        self.disk_mapping = {}

    def check(self):
        self.disk_mapping = get_disks_with_identifiers()
        self.add_disk_to_charts(self.disk_mapping.values())
        return True

    def get_data(self):
        disk_data = get_disk_stats(self.disk_mapping)
        disk_data_len = len(disk_data)
        current_disk_mapping_len = len(self.disk_mapping)
        if disk_data_len != current_disk_mapping_len:
            # This means that some disk has been added/removed
            self.disk_mapping = get_disks_with_identifiers()
            # Now that we have updated our mapping, we would like to normalize the identifier
            # for the disk which was added, for removal case we don't care as it is fine
            new_disks = []
            if disk_data_len > current_disk_mapping_len:
                for new_disk in filter(lambda d: not d.startswith('{'), list(disk_data)):
                    # We still use .get() here for safety, ideally we should have the identifier
                    # but for whatever reason that didn't happen, we will then report it as such
                    new_identifier = self.disk_mapping.get(new_disk, new_disk)
                    disk_data[new_identifier] = disk_data.pop(new_disk)
                    new_disks.append(new_identifier)

                self.add_disk_to_charts(new_disks)

        disks_stats = {}
        for disk_id, disks_io in disk_data.items():
            for op, value in disks_io.items():
                stat_id = f'{disk_id}.{op}'
                if op == 'busy':
                    disks_stats[stat_id] = value
                else:
                    # We maintain last stats as the data we get is total read/written etc
                    # However what we want to report is the difference to say that this much i/o
                    # happened
                    if self.last_stats.get(stat_id) is not None:
                        disks_stats[stat_id] = value - self.last_stats[stat_id]
                    else:
                        # For this iteration it will be 0 as we can otherwise report huge values
                        # which won't be accurate obviously
                        disks_stats[stat_id] = 0
                    self.last_stats[stat_id] = value

        return disks_stats

    def add_disk_to_charts(self, disk_ids):
        for disk_id in disk_ids:
            if disk_id in self.charts:
                continue

            self.charts.add_chart([
                f'io.{disk_id}', disk_id, disk_id, 'KiB/s',
                'disk.io',
                f'Read/Write for disk {disk_id}', 'line',
            ])
            self.charts.add_chart([
                f'ops.{disk_id}', disk_id, disk_id, 'Operation/s',
                'disk.ops',
                f'Complete read/write for disk {disk_id}', 'line',
            ])
            self.charts.add_chart([
                f'busy.{disk_id}', disk_id, disk_id, 'Milliseconds',
                'disk.busy',
                f'busy', 'line',
            ])
            self.charts[f'io.{disk_id}'].add_dimension([f'{disk_id}.reads'])
            self.charts[f'io.{disk_id}'].add_dimension([f'{disk_id}.writes'])
            self.charts[f'ops.{disk_id}'].add_dimension([f'{disk_id}.read_ops'])
            self.charts[f'ops.{disk_id}'].add_dimension([f'{disk_id}.write_ops'])
            self.charts[f'busy.{disk_id}'].add_dimension([f'{disk_id}.busy'])
