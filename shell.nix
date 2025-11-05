{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "mutooni-dev-shell";

  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.podman
    pkgs.slirp4netns
    pkgs.fuse-overlayfs
    pkgs.docker-compose
    pkgs.git
  ];

  shellHook = ''
    # Configuration des containers
    mkdir -p $HOME/.config/containers
    test -f $HOME/.config/containers/policy.json || echo '{"default":[{"type":"insecureAcceptAnything"}]}' > $HOME/.config/containers/policy.json
    test -f $HOME/.config/containers/registries.conf || echo 'unqualified-search-registries = ["docker.io"]' > $HOME/.config/containers/registries.conf
    
    # Configuration du virtualenv
    if [ ! -d .venv ]; then
      python -m venv .venv
    fi
    
    echo "✅ Environnement Nix pour Mutooni prêt."
    echo "�� Active ton environnement virtuel avec: source .venv/bin/activate"
  '';
}
