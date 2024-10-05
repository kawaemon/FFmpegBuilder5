import textwrap
def begin_stage_abs(pkg):
    k = f"""
        from base as {pkg}
        run git clone https://gitlab.archlinux.org/archlinux/packaging/packages/{pkg}.git --depth=1
        workdir {pkg}
    """
    return textwrap.dedent(k)

def cache(dir, user=False):
    user = "uid=1000,gid=1000," if user else ""
    return f"--mount=type=cache,sharing=locked,{user}target={dir}"

def cache_pacman():
    pdir = "/var/cache/pacman"
    return cache(pdir)

def cache_makepkg_git(gitdir):
    return cache(gitdir, user=True)

def run_pacman_S(pkgs):
    return f"run {cache_pacman()} pacman -S --noconfirm --needed {pkgs}"

def run(cmd):
    return f"run {" && ".join(cmd)}"

def replace(file, fr, to):
    return f"sed -i \"s|{fr}|{to}|g\" {file}"

stages = []

stages.append(f"""
  from archlinux as base
  workdir /app
  arg UID=1000
  arg GID=1000
  run echo 'Server = https://mirrors.cat.net/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
  run {cache_pacman()} pacman -Sy --noconfirm archlinux-keyring
  {run_pacman_S("base-devel git sudo")}
  {run([
      "groupadd -g ${GID} kawak",
      "useradd -m kawak -u ${UID} -g kawak",
      "passwd -d kawak",
      "echo '%kawak ALL=(ALL:ALL) ALL' >> /etc/sudoers"
  ])}
  shell ["/usr/bin/bash", "-c"]
  user kawak
  workdir /home/kawak
""")

stages.append(f"""
  {begin_stage_abs('ffmpeg')}

  run echo 'options=(!strip staticlibs)' >> PKGBUILD

  run {cache_pacman()} {cache_makepkg_git("ffmpeg")} \\
      makepkg -so --noconfirm --skippgpcheck

  run {cache_pacman()} sudo pacman -S --noconfirm vim

  {run([
      "sed -zi 's|\\\\\\n||g' PKGBUILD",
      replace(
          "PKGBUILD",
            "./configure.*",
              textwrap.dedent("""
                  ./configure --prefix=/usr --disable-debug --disable-stripping \
                  --enable-gpl --disable-shared --enable-static --enable-version3 --enable-lto \
                  --disable-{sdl2,xlib,libxcb{,-{shm,xfixes,shape}}} \
                  --extra-ldflags=-Wl,-Bstatic --extra-libs=-Wl,-Bdynamic
              """.strip())),
  ])}

  run {cache_makepkg_git("ffmpeg")} \\
      source /etc/profile \\
   && makepkg -e --nocheck MAKEFLAGS=-j$(nproc) # || (cat src/ffmpeg/ffbuild/config.log && fail)

  user root
  run mv /home/kawak/ffmpeg/ffmpeg-*.pkg.* /ffmpeg
""")

stages.append(f"""
  from base as ldd
  user root
  copy --from=ffmpeg /ffmpeg /
  run {cache_pacman()} pacman -U --noconfirm /ffmpeg
  run ldd $(which ffmpeg) && fail
""")

for stages in stages:
    print(textwrap.dedent(stages))
    print()
    print("# ---")
    print()


"""
        linux-vdso.so.1 (0x000075332e11e000)
        libavdevice.so.61 => /usr/lib/libavdevice.so.61 (0x000075332e08c000)
        libavfilter.so.10 => /usr/lib/libavfilter.so.10 (0x000075332da00000)
        libavformat.so.61 => /usr/lib/libavformat.so.61 (0x000075332d600000)
        libavcodec.so.61 => /usr/lib/libavcodec.so.61 (0x000075332c000000)
        libpostproc.so.58 => /usr/lib/libpostproc.so.58 (0x000075332e077000)
        libswresample.so.5 => /usr/lib/libswresample.so.5 (0x000075332e058000)
        libswscale.so.8 => /usr/lib/libswscale.so.8 (0x000075332dfb2000)
        libavutil.so.59 => /usr/lib/libavutil.so.59 (0x000075332ae00000)
        libm.so.6 => /usr/lib/libm.so.6 (0x000075332d911000)
        libc.so.6 => /usr/lib/libc.so.6 (0x000075332ac0f000)
        libraw1394.so.11 => /usr/lib/libraw1394.so.11 (0x000075332dfa0000)
        libavc1394.so.0 => /usr/lib/libavc1394.so.0 (0x000075332df99000)
        librom1394.so.0 => /usr/lib/librom1394.so.0 (0x000075332df91000)
        libiec61883.so.0 => /usr/lib/libiec61883.so.0 (0x000075332df83000)
        libjack.so.0 => /usr/lib/libjack.so.0 (0x000075332df30000)
        libdrm.so.2 => /usr/lib/libdrm.so.2 (0x000075332df19000)
        libxcb.so.1 => /usr/lib/libxcb.so.1 (0x000075332deee000)
        libxcb-shm.so.0 => /usr/lib/libxcb-shm.so.0 (0x000075332dee9000)
        libxcb-shape.so.0 => /usr/lib/libxcb-shape.so.0 (0x000075332dee1000)
        libxcb-xfixes.so.0 => /usr/lib/libxcb-xfixes.so.0 (0x000075332d908000)
        libasound.so.2 => /usr/lib/libasound.so.2 (0x000075332d51c000)
        libGL.so.1 => /usr/lib/libGL.so.1 (0x000075332bf7a000)
        libpulse.so.0 => /usr/lib/libpulse.so.0 (0x000075332d8b3000)
        libSDL2-2.0.so.0 => /usr/lib/libSDL2-2.0.so.0 (0x000075332aa3c000)
        libv4l2.so.0 => /usr/lib/libv4l2.so.0 (0x000075332d8a2000)
        libXv.so.1 => /usr/lib/libXv.so.1 (0x000075332d515000)
        libX11.so.6 => /usr/lib/libX11.so.6 (0x000075332a8fb000)
        libXext.so.6 => /usr/lib/libXext.so.6 (0x000075332d500000)
        libbs2b.so.0 => /usr/lib/libbs2b.so.0 (0x000075332d4f8000)
        librubberband.so.2 => /usr/lib/librubberband.so.2 (0x000075332a8a5000)
        libharfbuzz.so.0 => /usr/lib/libharfbuzz.so.0 (0x000075332a786000)
        libfribidi.so.0 => /usr/lib/libfribidi.so.0 (0x000075332d4d8000)
        libplacebo.so.349 => /usr/lib/libplacebo.so.349 (0x000075332a67c000)
        libvmaf.so.3 => /usr/lib/libvmaf.so.3 (0x000075332a578000)
        libass.so.9 => /usr/lib/libass.so.9 (0x000075332bf3b000)
        libva.so.2 => /usr/lib/libva.so.2 (0x000075332a542000)
        libvidstab.so.1.2 => /usr/lib/libvidstab.so.1.2 (0x000075332d4c1000)
        libzmq.so.5 => /usr/lib/libzmq.so.5 (0x000075332a45d000)
        libzimg.so.2 => /usr/lib/libzimg.so.2 (0x000075332a38e000)
        libglslang.so.14 => /usr/lib/libglslang.so.14 (0x000075332a000000)
        libSPIRV.so.14 => /usr/lib/libSPIRV.so.14 (0x0000753329400000)
        libOpenCL.so.1 => /usr/lib/libOpenCL.so.1 (0x000075332a364000)
        libfontconfig.so.1 => /usr/lib/libfontconfig.so.1 (0x000075332a314000)
        libfreetype.so.6 => /usr/lib/libfreetype.so.6 (0x0000753329f36000)
        libvpl.so.2 => /usr/lib/libvpl.so.2 (0x000075332a2b8000)
        libz.so.1 => /usr/lib/libz.so.1 (0x0000753329f1d000)
        libdvdnav.so.4 => /usr/lib/libdvdnav.so.4 (0x0000753329f06000)
        libdvdread.so.8 => /usr/lib/libdvdread.so.8 (0x0000753329ee5000)
        libxml2.so.2 => /usr/lib/libxml2.so.2 (0x00007533292b3000)
        libbz2.so.1.0 => /usr/lib/libbz2.so.1.0 (0x000075332d4aa000)
        libmodplug.so.1 => /usr/lib/libmodplug.so.1 (0x0000753329125000)
        libopenmpt.so.0 => /usr/lib/libopenmpt.so.0 (0x0000753328f35000)
        libbluray.so.2 => /usr/lib/libbluray.so.2 (0x0000753329e88000)
        libgmp.so.10 => /usr/lib/libgmp.so.10 (0x0000753328e8f000)
        libgnutls.so.30 => /usr/lib/libgnutls.so.30 (0x0000753328c93000)
        libsrt.so.1.5 => /usr/lib/libsrt.so.1.5 (0x0000753328bba000)
        libssh.so.4 => /usr/lib/libssh.so.4 (0x0000753328b43000)
        libvpx.so.9 => /usr/lib/libvpx.so.9 (0x0000753328800000)
        libwebpmux.so.3 => /usr/lib/libwebpmux.so.3 (0x000075332bf2d000)
        liblzma.so.5 => /usr/lib/liblzma.so.5 (0x0000753329e55000)
        libdav1d.so.7 => /usr/lib/libdav1d.so.7 (0x0000753328621000)
        libopencore-amrwb.so.0 => /usr/lib/libopencore-amrwb.so.0 (0x0000753328b2d000)
        librsvg-2.so.2 => /usr/lib/librsvg-2.so.2 (0x0000753328000000)
        libgobject-2.0.so.0 => /usr/lib/libgobject-2.0.so.0 (0x00007533285c1000)
        libcairo.so.2 => /usr/lib/libcairo.so.2 (0x0000753327ec9000)
        libglib-2.0.so.0 => /usr/lib/libglib-2.0.so.0 (0x0000753327d79000)
        libsnappy.so.1 => /usr/lib/libsnappy.so.1 (0x0000753329e46000)
        libaom.so.3 => /usr/lib/libaom.so.3 (0x0000753327400000)
        libgsm.so.1 => /usr/lib/libgsm.so.1 (0x0000753328b1e000)
        libjxl.so.0.11 => /usr/lib/libjxl.so.0.11 (0x0000753327000000)
        libjxl_threads.so.0.11 => /usr/lib/libjxl_threads.so.0.11 (0x000075332a2b2000)
        libmp3lame.so.0 => /usr/lib/libmp3lame.so.0 (0x000075332854a000)
        libopencore-amrnb.so.0 => /usr/lib/libopencore-amrnb.so.0 (0x0000753328520000)
        libopenjp2.so.7 => /usr/lib/libopenjp2.so.7 (0x0000753327d14000)
        libopus.so.0 => /usr/lib/libopus.so.0 (0x0000753326a00000)
        librav1e.so.0.7 => /usr/lib/librav1e.so.0.7 (0x0000753326600000)
        libspeex.so.1 => /usr/lib/libspeex.so.1 (0x0000753328504000)
        libSvtAv1Enc.so.2 => /usr/lib/libSvtAv1Enc.so.2 (0x000075331de00000)
        libtheoraenc.so.1 => /usr/lib/libtheoraenc.so.1 (0x0000753327cdc000)
        libtheoradec.so.1 => /usr/lib/libtheoradec.so.1 (0x00007533284ea000)
        libvorbis.so.0 => /usr/lib/libvorbis.so.0 (0x0000753327cae000)
        libvorbisenc.so.2 => /usr/lib/libvorbisenc.so.2 (0x0000753327355000)
        libwebp.so.7 => /usr/lib/libwebp.so.7 (0x00007533272e3000)
        libx264.so.164 => /usr/lib/libx264.so.164 (0x000075331da00000)
        libx265.so.209 => /usr/lib/libx265.so.209 (0x000075331c600000)
        libxvidcore.so.4 => /usr/lib/libxvidcore.so.4 (0x00007533264f3000)
        libsoxr.so.0 => /usr/lib/libsoxr.so.0 (0x0000753326f9f000)
        libva-drm.so.2 => /usr/lib/libva-drm.so.2 (0x00007533284e5000)
        libva-x11.so.2 => /usr/lib/libva-x11.so.2 (0x00007533284de000)
        libvdpau.so.1 => /usr/lib/libvdpau.so.1 (0x0000753327ca9000)
        /lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x000075332e120000)
        libdb-5.3.so => /usr/lib/libdb-5.3.so (0x000075331c43d000)
        libstdc++.so.6 => /usr/lib/libstdc++.so.6 (0x000075331c000000)
        libgcc_s.so.1 => /usr/lib/libgcc_s.so.1 (0x0000753327c7b000)
        libXau.so.6 => /usr/lib/libXau.so.6 (0x0000753327c76000)
        libXdmcp.so.6 => /usr/lib/libXdmcp.so.6 (0x00007533272db000)
        libGLdispatch.so.0 => /usr/lib/libGLdispatch.so.0 (0x0000753326948000)
        libGLX.so.0 => /usr/lib/libGLX.so.0 (0x0000753326f6d000)
        libpulsecommon-17.0.so => /usr/lib/pulseaudio/libpulsecommon-17.0.so (0x000075332646c000)
        libdbus-1.so.3 => /usr/lib/libdbus-1.so.3 (0x000075331ddaf000)
        libv4lconvert.so.0 => /usr/lib/libv4lconvert.so.0 (0x000075331dd36000)
        libfftw3.so.3 => /usr/lib/libfftw3.so.3 (0x000075331bc00000)
        libsamplerate.so.0 => /usr/lib/libsamplerate.so.0 (0x000075331c2cf000)
        libgraphite2.so.3 => /usr/lib/libgraphite2.so.3 (0x0000753326f4b000)
        libunwind.so.8 => /usr/lib/libunwind.so.8 (0x0000753326f31000)
        libshaderc_shared.so.1 => /usr/lib/libshaderc_shared.so.1 (0x0000753326929000)
        libglslang-default-resource-limits.so.14 => /usr/lib/libglslang-default-resource-limits.so.14 (0x00007533272d1000)
        libvulkan.so.1 => /usr/lib/libvulkan.so.1 (0x000075331d97c000)
        liblcms2.so.2 => /usr/lib/liblcms2.so.2 (0x000075331dcce000)
        libdovi.so.3 => /usr/lib/libdovi.so.3 (0x000075331d8f3000)
        libunibreak.so.6 => /usr/lib/libunibreak.so.6 (0x000075332644a000)
        libgomp.so.1 => /usr/lib/libgomp.so.1 (0x000075331bfad000)
        libsodium.so.26 => /usr/lib/libsodium.so.26 (0x000075331bf4e000)
        libpgm-5.3.so.0 => /usr/lib/libpgm-5.3.so.0 (0x000075331bf04000)
        libSPIRV-Tools-opt.so => /usr/lib/libSPIRV-Tools-opt.so (0x000075331b800000)
        libSPIRV-Tools.so => /usr/lib/libSPIRV-Tools.so (0x000075331ba89000)
        libexpat.so.1 => /usr/lib/libexpat.so.1 (0x000075331c2a5000)
        libpng16.so.16 => /usr/lib/libpng16.so.16 (0x000075331bec9000)
        libbrotlidec.so.1 => /usr/lib/libbrotlidec.so.1 (0x0000753326f22000)
        libicuuc.so.75 => /usr/lib/libicuuc.so.75 (0x000075331b606000)
        libmpg123.so.0 => /usr/lib/libmpg123.so.0 (0x000075331be6d000)
        libvorbisfile.so.3 => /usr/lib/libvorbisfile.so.3 (0x00007533272c4000)
        libp11-kit.so.0 => /usr/lib/libp11-kit.so.0 (0x000075331b4a3000)
        libidn2.so.0 => /usr/lib/libidn2.so.0 (0x000075331be4b000)
        libunistring.so.5 => /usr/lib/libunistring.so.5 (0x000075331b2f3000)
        libtasn1.so.6 => /usr/lib/libtasn1.so.6 (0x000075331c290000)
        libhogweed.so.6 => /usr/lib/libhogweed.so.6 (0x000075331ba40000)
        libnettle.so.8 => /usr/lib/libnettle.so.8 (0x000075331b29c000)
        libcrypto.so.3 => /usr/lib/libcrypto.so.3 (0x000075331ac00000)
        libgdk_pixbuf-2.0.so.0 => /usr/lib/libgdk_pixbuf-2.0.so.0 (0x000075331b258000)
        libgio-2.0.so.0 => /usr/lib/libgio-2.0.so.0 (0x000075331aa31000)
        libpangocairo-1.0.so.0 => /usr/lib/libpangocairo-1.0.so.0 (0x000075331be3b000)
        libpango-1.0.so.0 => /usr/lib/libpango-1.0.so.0 (0x000075331b1ef000)
        libffi.so.8 => /usr/lib/libffi.so.8 (0x000075331be30000)
        libXrender.so.1 => /usr/lib/libXrender.so.1 (0x000075331ba34000)
        libxcb-render.so.0 => /usr/lib/libxcb-render.so.0 (0x000075331b1e0000)
        libpixman-1.so.0 => /usr/lib/libpixman-1.so.0 (0x000075331b136000)
        libpcre2-8.so.0 => /usr/lib/libpcre2-8.so.0 (0x000075331a992000)
        libjxl_cms.so.0.11 => /usr/lib/libjxl_cms.so.0.11 (0x000075331b0ff000)
        libhwy.so.1 => /usr/lib/libhwy.so.1 (0x000075331b0f3000)
        libbrotlienc.so.1 => /usr/lib/libbrotlienc.so.1 (0x000075331a8e0000)
        libogg.so.0 => /usr/lib/libogg.so.0 (0x000075331c286000)
        libsharpyuv.so.0 => /usr/lib/libsharpyuv.so.0 (0x000075331b0ea000)
        libmvec.so.1 => /usr/lib/libmvec.so.1 (0x000075331a7e8000)
        libXfixes.so.3 => /usr/lib/libXfixes.so.3 (0x000075331b0e2000)
        libX11-xcb.so.1 => /usr/lib/libX11-xcb.so.1 (0x000075331dcc9000)
        libxcb-dri3.so.0 => /usr/lib/libxcb-dri3.so.0 (0x000075331b0db000)
        libsndfile.so.1 => /usr/lib/libsndfile.so.1 (0x000075331a761000)
        libsystemd.so.0 => /usr/lib/libsystemd.so.0 (0x000075331a66d000)
        libasyncns.so.0 => /usr/lib/libasyncns.so.0 (0x000075331b0d3000)
        libjpeg.so.8 => /usr/lib/libjpeg.so.8 (0x000075331a5cf000)
        libbrotlicommon.so.1 => /usr/lib/libbrotlicommon.so.1 (0x000075331a5ac000)
        libicudata.so.75 => /usr/lib/libicudata.so.75 (0x0000753318800000)
        libgmodule-2.0.so.0 => /usr/lib/libgmodule-2.0.so.0 (0x000075331a5a5000)
        libtiff.so.6 => /usr/lib/libtiff.so.6 (0x0000753318773000)
        libmount.so.1 => /usr/lib/libmount.so.1 (0x000075331a556000)
        libpangoft2-1.0.so.0 => /usr/lib/libpangoft2-1.0.so.0 (0x0000753318757000)
        libthai.so.0 => /usr/lib/libthai.so.0 (0x000075331874c000)
        libFLAC.so.12 => /usr/lib/libFLAC.so.12 (0x0000753318708000)
        libcap.so.2 => /usr/lib/libcap.so.2 (0x00007533186fc000)
        libzstd.so.1 => /usr/lib/libzstd.so.1 (0x000075331861d000)
        libjbig.so.2.1 => /usr/lib/libjbig.so.2.1 (0x000075331860f000)
        libblkid.so.1 => /usr/lib/libblkid.so.1 (0x00007533185d6000)
        libdatrie.so.1 => /usr/lib/libdatrie.so.1 (0x00007533185cd000)
"""
