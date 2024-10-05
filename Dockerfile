
from archlinux as base
workdir /app
arg UID=1000
arg GID=1000
run echo 'Server = https://mirrors.cat.net/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
run --mount=type=cache,sharing=locked,target=/var/cache/pacman pacman -Sy --noconfirm archlinux-keyring
run --mount=type=cache,sharing=locked,target=/var/cache/pacman pacman -S --noconfirm --needed base-devel git sudo
run groupadd -g ${GID} kawak && useradd -m kawak -u ${UID} -g kawak && passwd -d kawak && echo '%kawak ALL=(ALL:ALL) ALL' >> /etc/sudoers
shell ["/usr/bin/bash", "-c"]
user kawak
workdir /home/kawak


# ---



from base as ffmpeg
run git clone https://gitlab.archlinux.org/archlinux/packaging/packages/ffmpeg.git --depth=1
workdir ffmpeg


  run echo 'options=(!strip staticlibs)' >> PKGBUILD

  run --mount=type=cache,sharing=locked,target=/var/cache/pacman --mount=type=cache,sharing=locked,uid=1000,gid=1000,target=ffmpeg \
      makepkg -so --noconfirm --skippgpcheck

  run --mount=type=cache,sharing=locked,target=/var/cache/pacman sudo pacman -S --noconfirm vim

  run sed -zi 's|\\\n||g' PKGBUILD && sed -i "s|./configure.*|./configure --prefix=/usr --disable-debug --disable-stripping                   --enable-gpl --disable-shared --enable-static --enable-version3 --enable-lto                   --disable-{sdl2,xlib,libxcb{,-{shm,xfixes,shape}}}                   --extra-ldflags=-Wl,-Bstatic --extra-libs=-Wl,-Bdynamic|g" PKGBUILD

  run --mount=type=cache,sharing=locked,uid=1000,gid=1000,target=ffmpeg \
      source /etc/profile \
   && makepkg -e --nocheck MAKEFLAGS=-j$(nproc) # || (cat src/ffmpeg/ffbuild/config.log && fail)

  user root
  run mv /home/kawak/ffmpeg/ffmpeg-*.pkg.* /ffmpeg


# ---


from base as ldd
user root
copy --from=ffmpeg /ffmpeg /
run --mount=type=cache,sharing=locked,target=/var/cache/pacman pacman -U --noconfirm /ffmpeg
run ldd $(which ffmpeg) && fail


# ---

