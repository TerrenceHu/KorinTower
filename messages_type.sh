
# 对导出 channel 消息进行负采样：长度较短的消息，不太可能是反馈报告，按5%采样；否则按10%采样 
awk -F"\t" 'BEGIN{srand();}{if(length($3)<200) {if(rand()<0.05) print;} else {if(rand()<0.1) print;}}' channel_messages__202502020945.csv > tmp/channel_messages.csv
# 用LLM 对message进行判断（标注）
python src/gen_message_type_data.py tmp/channel_messages.csv > tmp/channel_messages

awk -F"\t" '{print $3"\t"2}' _channel_messages__202502022351.csv > tmp/bad_reports

# 显性加上文本长度字段
awk -F"\t" '{l=length($1); if(l<100) t="L100"; else if(l<200) t="L200"; else if(l<500) t="L500"; else if(l<1000) t="L1000"; else t="L2000"; print t" "$1"\t"$2;}' tmp/channel_messages tmp/bad_reports | sort -R > data/messages_type

head -400 data/messages_type > data/messages_type.train
tail -107 data/messages_type > data/messages_type.test
