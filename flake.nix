{
  description = "Sonata, a Python 2 / GTK 2 client for MPD";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ ./package.nix ];
      systems = [ "x86_64-linux" ];
    };
}
