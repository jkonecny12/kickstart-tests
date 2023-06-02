#
# Copyright (C) 2023  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Radek Vykydal <rvykydal@redhat.com>

# Ignore unused variable parsed out by tooling scripts as test tags metadata
# shellcheck disable=SC2034
TESTTYPE="network"

. ${KSTESTDIR}/functions.sh

# Installer image is defined in kickstart via url command
stage2_from_ks() {
    echo "true"
}

# The test needs more RAM because installer image is downloaded from network
get_required_ram() {
    echo "2572"
}

replace_ks_basearch() {
    ks=$1

    # inst.stage2 command can't cope with $basearch variable in KSTEST_URL
    sed -i -e 's#\(^url.*\)\$basearch#\1x86_64#' ${ks}

    echo $ks
}

replace_ks_url() {
    ks=$1
    http_ip=$2

    #replace @HTTP_LOCAL_SERVER@ with local server serving stage2 image and empty repositories
    sed -i -e "s#\(^url.*\)\@HTTP_LOCAL_SERVER@#\1$2#" ${ks}

    echo $ks
}

prepare() {
    ks=$1
    tmpdir=$2

    # Copy the stage2 to a directory in tmpdir
    mkdir -p ${tmpdir}/http/images

    isoinfo -i ${tmpdir}/$(basename ${IMAGE}) -x "/IMAGES/INSTALL.IMG;1" > ${tmpdir}/http/images/install.img
    createrepo_c -q ${tmpdir}/http

    # Start a http server to serve the included file
    start_httpd ${tmpdir}/http $tmpdir

    ks=$(replace_ks_basearch $ks)
    ks=$(replace_ks_url $ks $httpd_url)

    echo "${ks}"
}
