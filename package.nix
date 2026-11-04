{ inputs, ... }:
{
  perSystem =
    { system, ... }:
    let
      pkgs = import inputs.nixpkgs {
        inherit system;
        # Allow only the legacy interpreter and its development environment.
        config.permittedInsecurePackages = [
          "python-2.7.18.12"
          "python-2.7.18.12-env"
        ];
      };
      # Python 2 package set shared by the package and the dev shell.
      python = pkgs.python2.override {
        packageOverrides = _: previous: {
          # Cairo's legacy pytest closure has broken Python 2 dependencies.
          pycairo = previous.pycairo.overridePythonAttrs {
            doCheck = false;
            checkPhase = "";
          };
        };
      };
      # Avoid incompatible host fontconfig files in both launch modes.
      fontsConf = pkgs.makeFontsConf {
        fontDirectories = [ pkgs.dejavu_fonts ];
        includes = [ ];
      };
      # Legacy MPD client library; current python-mpd2 no longer supports Python 2.
      mpd = python.pkgs.buildPythonPackage rec {
        pname = "python-mpd";
        version = "0.3.0";
        format = "setuptools";
        src = pkgs.fetchPypi {
          inherit pname version;
          hash = "sha256-AoEuuh0uD0bjdFf1pvojuiA2IuS8qwoZsmXmawjNIbQ=";
        };
      };
      # Sonata itself, built with the original setup.py (includes the mmkeys C extension).
      sonata = python.pkgs.buildPythonApplication {
        pname = "sonata";
        version = "1.6.2.1";
        format = "setuptools";
        src = pkgs.lib.cleanSource ./.;

        # gettext compiles translations; pkg-config locates GTK 2 for mmkeys.
        nativeBuildInputs = [
          pkgs.gettext
          pkgs.pkg-config
          pkgs.wrapGAppsNoGuiHook
        ];
        # Runtime Python dependencies (PyGTK pulls in GTK 2, PyGObject and Cairo).
        propagatedBuildInputs = [
          mpd
          python.pkgs.pygtk
        ];

        # The PyGObject 2 headers rely on GCC's pre-GCC-10 common-symbol behavior.
        env.NIX_CFLAGS_COMPILE = "-fcommon";

        # Put GTK resources, pinned fonts and the hicolor icon theme into the single Python wrapper.
        dontWrapGApps = true;
        preFixup = ''
          makeWrapperArgs+=("''${gappsWrapperArgs[@]}"
            --set-default FONTCONFIG_FILE "${fontsConf}"
            --prefix XDG_DATA_DIRS : "${pkgs.hicolor-icon-theme}/share"
          )
        '';

        meta = {
          description = "Elegant GTK 2 client for the Music Player Daemon";
          license = pkgs.lib.licenses.gpl3Plus;
          mainProgram = "sonata"; # used by `nix run`
        };
      };
    in
    {
      packages.default = sonata;
      # `nix flake check` builds the package.
      checks.sonata = sonata;
      # Make `python sonata.py` use the same interpreter and dependencies.
      devShells.default = pkgs.mkShell {
        inputsFrom = [ sonata ];
        packages = [
          (python.withPackages (_: sonata.propagatedBuildInputs))
        ];
        # Same font and icon setup as the wrapped `sonata` binary.
        FONTCONFIG_FILE = fontsConf;
        shellHook = ''
          export XDG_DATA_DIRS="${pkgs.hicolor-icon-theme}/share''${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
        '';
      };
      formatter = pkgs.nixfmt;
    };
}
