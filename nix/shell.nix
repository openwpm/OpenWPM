{ pkgs ? import <nixpkgs> {} }:

let
  packages = with pkgs; [
    # Build essentials
    stdenv.cc.cc.lib
    gcc
    gnumake
    pkg-config
    zlib
    openssl

    # Python build dependencies
    libffi
    readline
    ncurses
    bzip2
    xz
    sqlite

    # Firefox dependencies
    gtk3
    glib
    atk
    gdk-pixbuf
    pciutils
    dbus-glib
    libGL
    libGLU
    alsa-lib
    libpulseaudio
    ffmpeg
    pango
    cairo
    freetype
    fontconfig

    # X11 libraries
    libx11
    libxext
    libxrender
    libxtst
    libxi
    libxcomposite
    libxcursor
    libxdamage
    libxfixes
    libxrandr
    libxcb
    xvfb

    # Utilities
    git
    which
    curl
    wget
    file
    gnugrep
    coreutils
    bashInteractive

    # Node.js for extension build
    nodejs_22
  ];

  libraryPath = pkgs.lib.makeLibraryPath (with pkgs; [
    stdenv.cc.cc.lib
    zlib
    libGL
    glib
    gtk3
    atk
    gdk-pixbuf
    pciutils
    alsa-lib
    libpulseaudio
    libx11
    libxext
    libxrender
    libxtst
    libxcomposite
    libxcursor
    libxdamage
    libxfixes
    libxrandr
    dbus-glib
    pango
    cairo
    freetype
    fontconfig
  ]);

  fhsEnv = pkgs.buildFHSEnv {
    name = "openwpm";
    targetPkgs = _: packages;
    profile = ''
      export LD_LIBRARY_PATH="${libraryPath}:$LD_LIBRARY_PATH"
      export PATH="$HOME/.conda/bin:$PATH"
      source "$HOME/.conda/etc/profile.d/conda.sh"
    '';
    runScript = let
      condaInit = pkgs.writeText "conda-init.sh" ''
        set -h  # Enable command hashing
        source "$HOME/.conda/etc/profile.d/conda.sh"
        conda activate openwpm
      '';
    in pkgs.writeShellScript "openwpm-shell" ''
      export BASH_ENV="${condaInit}"
      exec bash --rcfile "${condaInit}" "$@"
    '';
  };

in pkgs.mkShell {
  packages = [ fhsEnv ];
  shellHook = ''
    exec openwpm
  '';
}
