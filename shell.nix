{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Define the packages available in the environment
  packages = [
    (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
      dns
      requests
      openai
    ]))
  ];
}
