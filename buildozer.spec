[app]
title = Факты о ВОВ
package.name = warfacts
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.0
requirements = python3,kivy==2.1.0,setuptools,wheel
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.minapi = 21
android.api = 33
android.ndk = 28c
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.graphics_api = gl
android.allow_backup = True
android.accept_sdk_license = True
android.enable_androidx = True
android.copy_libs = 1
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1