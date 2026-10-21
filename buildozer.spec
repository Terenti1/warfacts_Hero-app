[app]
title = Герои Беларуси
package.name = belarusheroes
package.domain = org.belarusheroes
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.0

requirements = hostpython3==3.10.12,python3==3.10.12,kivy,requests,urllib3,certifi,charset-normalizer,idna

orientation = portrait
fullscreen = 1

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a
android.graphics_api = gl
android.accept_sdk_license = True
android.allow_backup = True
android.debug_artifact = apk
android.manifest.orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 0
