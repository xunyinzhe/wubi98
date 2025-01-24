# 说明

chars.txt 规范汉字

words.txt 所有的词

wubi.txt  五笔编码


## 简码

```powershell
# 生成包含字频的码表
python .\tool.py freq .\wubi.txt .\wubi_with_freq.txt
# 生成二级简码候选字
Get-Content .\wubi_with_freq.txt | ForEach-Object { $cols=$_.Split(); $cols[1]=$cols[1].Substring(0,2); $cols -join "`t" } | Group-Object { $_.Split()[1] } | ForEach-Object { $code = $_.Name; $chars = $_.Group | Sort-Object { [int]$_.Split()[2] } -Descending | ForEach-Object { $_.Split()[0] } | Select-Object -First 40 | Join-String; $code + "`t" + $chars } > jm.txt
```
