# vim: ft=dockerfile
from archlinux

run echo 'Server = https://mirrors.cat.net/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
run --mount=type=cache,target=/var/cache/pacman,sharing=locked \
    pacman -Sy --noconfirm archlinux-keyring \
 && pacman -Su --noconfirm --needed base base-devel git tmux vim htop

run useradd -m -G wheel kawak \
  && passwd -d kawak \
  && echo '%wheel ALL=(ALL:ALL) ALL' >> /etc/sudoers
  && echo 'source /etc/profile' >> /home/kawak/.bashrc

copy tmux.conf /root/.tmux.conf
copy tmux.conf /home/kawak/.tmux.conf

run \
  && sed -i 's/strip/!strip/g' /etc/makepkg.conf \
  && sed -i 's/lto/!lto/g' /etc/makepkg.conf \
  && sed -i 's/-march=x86-64 -mtune=generic/-march=native/g' /etc/makepkg.conf

user kawak
