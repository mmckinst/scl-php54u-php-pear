%{?scl:%scl_package php-pear}
%{!?scl:%global pkg_name %{name}}

%global peardir %{_datadir}/pear

%global xmlrpcver 1.5.1
%global getoptver 1.2.3
%global arctarver 1.3.3
%global structver 1.0.2
%global xmlutil   1.2.1

%define basever 1.9
Summary: PHP Extension and Application Repository framework
Name: %{?scl_prefix}php-pear
Version: 1.9.4
Release: 3.ius%{?dist}
Epoch: 1
License: PHP
Group: Development/Languages
URL: http://pear.php.net/package/PEAR
Source0: http://download.pear.php.net/package/PEAR-%{version}.tgz
# wget http://cvs.php.net/viewvc.cgi/pear-core/install-pear.php?revision=1.39 -O install-pear.php
Source1: install-pear.php
Source2: relocate.php
Source3: strip.php
Source4: LICENSE
Source10: pear.sh
Source11: pecl.sh
Source12: peardev.sh
Source13: macros.pear
Source20: http://pear.php.net/get/XML_RPC-%{xmlrpcver}.tgz
Source21: http://pear.php.net/get/Archive_Tar-%{arctarver}.tgz
Source22: http://pear.php.net/get/Console_Getopt-%{getoptver}.tgz
Source23: http://pear.php.net/get/Structures_Graph-%{structver}.tgz
Source24: http://pear.php.net/get/XML_Util-%{xmlutil}.tgz

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{?scl_prefix}php-cli, %{?scl_prefix}php-xml, gnupg
Provides: %{?scl_prefix}php-pear(Console_Getopt) = %{getoptver}
Provides: %{?scl_prefix}php-pear(Archive_Tar) = %{arctarver}
Provides: %{?scl_prefix}php-pear(PEAR) = %{version}
Provides: %{?scl_prefix}php-pear(Structures_Graph) = %{structver}
Provides: %{?scl_prefix}php-pear(XML_RPC) = %{xmlrpcver}
Provides: %{?scl_prefix}php-pear(XML_Util) = %{xmlutil}

# FIX ME: Should be removed before/after RHEL 5.6 is out
# See: https://bugs.launchpad.net/ius/+bug/691755


%description
PEAR is a framework and distribution system for reusable PHP
components.  This package contains the basic PEAR components.

%prep
%setup -cT -n %{name}-%{version}

# Create a usable PEAR directory (used by install-pear.php)
for archive in %{SOURCE0} %{SOURCE21} %{SOURCE22} %{SOURCE23} %{SOURCE24}
do
    tar xzf  $archive --strip-components 1 || tar xzf  $archive --strip-path 1
done
tar xzf %{SOURCE24} package.xml
mv package.xml XML_Util.xml

# apply patches on used PEAR during install
# -- no patch

%build
# This is an empty build section.

%install
rm -rf $RPM_BUILD_ROOT

export PHP_PEAR_SYSCONF_DIR=%{_sysconfdir}
export PHP_PEAR_SIG_KEYDIR=%{_sysconfdir}/pearkeys
export PHP_PEAR_SIG_BIN=%{_root_bindir}/gpg
export PHP_PEAR_INSTALL_DIR=%{peardir}

# 1.4.11 tries to write to the cache directory during installation
# so it's not possible to set a sane default via the environment.
# The ${PWD} bit will be stripped via relocate.php later.
export PHP_PEAR_CACHE_DIR=${PWD}%{_localstatedir}/cache/php-pear
export PHP_PEAR_TEMP_DIR=/var/tmp

install -d $RPM_BUILD_ROOT%{peardir} \
           $RPM_BUILD_ROOT%{_localstatedir}/cache/php-pear \
           $RPM_BUILD_ROOT%{_localstatedir}/www/html \
           $RPM_BUILD_ROOT%{peardir}/.pkgxml \
           $RPM_BUILD_ROOT%{_sysconfdir}/rpm \
           $RPM_BUILD_ROOT%{_sysconfdir}/pear

export INSTALL_ROOT=$RPM_BUILD_ROOT

%{_bindir}/php -n -dmemory_limit=32M -dshort_open_tag=0 -dsafe_mode=0 \
         -derror_reporting=E_ALL -ddetect_unicode=0 \
      %{SOURCE1} -d %{peardir} \
                 -c %{_sysconfdir}/pear \
                 -b %{_bindir} \
                 -w %{_localstatedir}/www/html \
                 %{SOURCE0} %{SOURCE21} %{SOURCE22} %{SOURCE23} %{SOURCE24} %{SOURCE20}

# Replace /usr/bin/* with simple scripts:
install -m 755 %{SOURCE10} $RPM_BUILD_ROOT%{_bindir}/pear
install -m 755 %{SOURCE11} $RPM_BUILD_ROOT%{_bindir}/pecl
install -m 755 %{SOURCE12} $RPM_BUILD_ROOT%{_bindir}/peardev
for exe in pear pecl peardev; do
    sed -e 's:/usr:%{_prefix}:' \
        -i $RPM_BUILD_ROOT%{_bindir}/$exe
done

# Sanitize the pear.conf
%{_bindir}/php -n %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf $RPM_BUILD_ROOT | 
  %{_bindir}/php -n %{SOURCE2} php://stdin $PWD > new-pear.conf
%{_bindir}/php -n %{SOURCE3} new-pear.conf ext_dir |
  %{_bindir}/php -n %{SOURCE3} php://stdin http_proxy > $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf

%{_bindir}/php -r "print_r(unserialize(substr(file_get_contents('$RPM_BUILD_ROOT%{_sysconfdir}/pear.conf'),17)));"

install -m 644 -c %{SOURCE4} LICENSE

install -m 644 -c %{SOURCE13} \
           $RPM_BUILD_ROOT%{_sysconfdir}/rpm/macros.pear     

# apply patches on installed PEAR tree
pushd $RPM_BUILD_ROOT%{peardir} 
# -- no patch
popd

# Why this file here ?
rm -rf $RPM_BUILD_ROOT/.depdb* $RPM_BUILD_ROOT/.lock $RPM_BUILD_ROOT/.channels $RPM_BUILD_ROOT/.filemap

# Need for re-registrying XML_Util
install -m 644 XML_Util.xml $RPM_BUILD_ROOT%{peardir}/.pkgxml/


%check
# Check that no bogus paths are left in the configuration, or in
# the generated registry files.
grep $RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep %{_libdir} $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep '"/tmp"' $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep /usr/local $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep -rl $RPM_BUILD_ROOT $RPM_BUILD_ROOT && exit 1


%clean
rm -rf $RPM_BUILD_ROOT
rm new-pear.conf


%triggerpostun -- php-pear-XML-Util
# re-register extension unregistered during postun of obsoleted php-pear-XML-Util
%{_bindir}/pear install --nodeps --soft --force --register-only %{pear_xmldir}/XML_Util.xml >/dev/null || :


%files
%defattr(-,root,root,-)
%{peardir}
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/pear.conf
%config %{_sysconfdir}/rpm/macros.pear
%dir %{_localstatedir}/cache/php-pear
%dir %{_localstatedir}/www/html
%dir %{_sysconfdir}/pear
%doc LICENSE README


%changelog
* Tue Jan 29 2014 Mark McKinstry <mmckinst@nexcess.net> - 1:1.9.4-3.ius
- convert to scl style rpm

* Tue Aug 21 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> - 1:1.9.4-2.ius
- Rebuilding against php54-5.4.6-2.ius as it is now using bundled PCRE.

* Thu Apr 19 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> - 1:1.9.4-1.ius
- Porting from php53u-pear to php54-pear
