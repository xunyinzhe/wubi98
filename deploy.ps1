# 把文件复制到Rime用户文件夹

$RimeUserPath = "$env:APPDATA\Rime"
# Remove-Item -Path $RimeUserPath
New-Item -ItemType Directory -Path $RimeUserPath -Force

Copy-Item -Force -Path "$PSScriptRoot\lua" -Destination $RimeUserPath\ -Recurse
Copy-Item -Force -Path "$PSScriptRoot\opencc" -Destination $RimeUserPath\ -Recurse
Copy-Item -Force -Path "$PSScriptRoot\default.custom.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\weasel.custom.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\numbers.schema.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\pinyin_simp.schema.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\pinyin_simp.dict.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\wubi98.schema.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\wubi98.dict.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\wubi98_ci.dict.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\wubi98_jm.dict.yaml" -Destination $RimeUserPath\
Copy-Item -Force -Path "$PSScriptRoot\wubi98_user.dict.yaml" -Destination $RimeUserPath\

# 重新部署
& 'C:\Program Files\Rime\weasel-0.16.3\WeaselDeployer.exe' /deploy