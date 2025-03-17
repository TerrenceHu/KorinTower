


        # channel 的 username 和 title 可能会变化，需要更新
        channel_item = self.channel_model.get_channel_by_id(channel.id)
        if channel.username != channel_item[1] or channel.title != channel_item[2]:
            self.channel_model.update_channel(channel.id, channel.username, channel.title, today_date)
            logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")


            # group 的 username 和 title 可能会变化，需要更新
            group_item = self.group_model.get_group_by_id(group.id)
            if group.username != group_item[1] or group.title != group_item[2]:
                self.group_model.update_group(group.id, group.username, group.title,
                                                  group.participants_count, today_date)
                logger.info(f"Update group {group.id},{group.username},{group.title}")