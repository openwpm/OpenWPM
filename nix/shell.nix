{ pkgs ? import <nixpkgs> {} }:

let
  # System libraries needed by Firefox (unbranded build in firefox-bin/)
  firefoxDeps = with pkgs; [
    gtk3
    glib
    atk
    gdk-pixbuf
    pango
    cairo
    freetype
    fontconfig
    dbus
    alsa-lib
    libx11
    libxcb
    libxext
    libxrender
    libxtst
    libxi
    libxcomposite
    libxcursor
    libxdamage
    libxfixes
    libxrandr
    xorg-server  # Xvfb for headless testing
    xvfb-run
  ];

  libraryPath = pkgs.lib.makeLibraryPath firefoxDeps;

  condaInit = pkgs.writeText "conda-init.sh" ''
    source /etc/profile
    source "$HOME/.conda/etc/profile.d/conda.sh"
    conda activate openwpm
    export LD_LIBRARY_PATH="${libraryPath}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  '';

  condaEnv = pkgs.conda.override {
    condaDeps = [];
    extraPkgs = firefoxDeps;
    runScript = toString (pkgs.writeShellScript "openwpm-shell" ''
      # Disable default Anaconda channels (we only use conda-forge)
      cat > "$HOME/.condarc" <<'CONDARC'
channels:
  - conda-forge
default_channels: []
CONDARC

      # Create openwpm env if it doesn't exist
      if ! conda env list | grep -q "^openwpm "; then
        echo "Creating openwpm conda environment..."
        PYTHONNOUSERSITE=True conda env create --yes -q -f environment.yaml
      fi

      exec bash --rcfile "${condaInit}" "$@"
    '');
  };

in pkgs.mkShell {
  packages = [ condaEnv ];
  shellHook = ''
    exec conda-shell
  '';
}
