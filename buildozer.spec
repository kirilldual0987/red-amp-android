[app]

# Application info
title = Red-Amp
package.name = redamp
package.domain = org.kirilldual0987

# Source code
source.dir = .
source.include_exts = py

# Version
version = 1.3

# Requirements
requirements = python3,kivy==2.2.1,android,pyjnius

# Application settings
orientation = portrait
fullscreen = 0

# Android specific
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 31
android.accept_sdk_license = True
android.arch = arm64-v8a
android.allow_backup = True

# Metadata
author = kirilldual0987
android.meta_data = com.google.android.gms.version=@integer/google_play_services_version

[buildozer]

# Log level
log_level = 1

# Warn on root
warn_on_root = 0
