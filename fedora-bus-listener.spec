Name:       {{{ git_dir_name }}}
Version:    {{{ git_dir_version }}}
Release:        1%{?dist}
Summary:        Listens to the Fedora message bus and dispatches EC2 builds on kernel updates

License:        AGPLv3
Source:     {{{ git_dir_pack }}}

BuildArch:      noarch
BuildRequires:  python3-devel

%generate_buildrequires
%pyproject_buildrequires

%description
Listens to the Fedora message bus and dispatches EC2 instance builds
whenever a stable kernel update is published for Fedora.

%prep
{{{ git_dir_setup_macro }}}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files fedora_bus_listener

install -Dm644 fedora-message-dispatcher@.service \
    %{buildroot}%{_unitdir}/fedora-message-dispatcher@.service

%post
%systemd_post fedora-message-dispatcher@.service

%preun
%systemd_preun fedora-message-dispatcher@.service

%postun
%systemd_postun_with_restart fedora-message-dispatcher@.service

%files -f %{pyproject_files}
%{_bindir}/fedora-bus-listener
%{_unitdir}/fedora-message-dispatcher@.service
