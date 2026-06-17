class Expando < Formula
  include Language::Python::Virtualenv

  desc "Privacy-first open-source text expander for macOS"
  homepage "https://github.com/andreapostiglione/expando"
  url "https://github.com/andreapostiglione/expando/archive/refs/tags/v1.4.0.tar.gz"
  version "1.4.0"
  sha256 "4d5230fad438d2f14fa92af13637730d7a7ddcad8690b96910627b95293ef9d8"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
    bin.install libexec/"bin/expando"

    (buildpath/"scripts/build-macos-app.sh").chmod 0555
    system buildpath/"scripts/build-macos-app.sh"
    prefix.install "Expando.app"
  end

  def caveats
    <<~EOS
      Grant Accessibility permission to:
        #{prefix}/Expando.app

      Run the onboarding wizard with:
        expando setup

      Install the launch agent with:
        expando run
      or use the menu bar app from Expando.app.
    EOS
  end

  test do
    system bin/"expando", "--version"
  end
end