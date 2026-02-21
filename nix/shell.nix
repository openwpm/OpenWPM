{ pkgs ? import <nixpkgs> {} }:

let
  # Libraries needed both as package inputs and on LD_LIBRARY_PATH at runtime
  sharedLibs = with pkgs; [
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
    dbus-glib
    pango
    cairo
    freetype
    fontconfig

    # X11 libraries
    libx11
    libxext
    libxrender
    libxtst
    libxcomposite
    libxcursor
    libxdamage
    libxfixes
    libxrandr
  ];

  packages = sharedLibs ++ (with pkgs; [
    # Build essentials
    gcc
    gnumake
    pkg-config
    openssl

    # Python build dependencies
    libffi
    readline
    ncurses
    bzip2
    xz
    sqlite

    # Additional Firefox dependencies
    ffmpeg

    # Additional X11 libraries
    libxi
    libxcb
    xvfb

    # Utilities
    git
    which
    wget
    gnugrep
    coreutils
    bashInteractive

    # Node.js for extension build
    nodejs_22
  ]);

  libraryPath = pkgs.lib.makeLibraryPath sharedLibs;

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
