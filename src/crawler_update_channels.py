


        # channel 的 username 和 title 可能会变化，需要更新
        channel_item = self.channel_model.get_channel_by_id(channel.id)
        if channel.username != channel_item[1] or channel.title != channel_item[2]:
            self.channel_model.update_channel(channel.id, channel.username, channel.title, today_date)
            logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")