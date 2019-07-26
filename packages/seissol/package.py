# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# by G. Brietzke March 2019

from spack import *
import llnl.util.tty as tty
import os
import inspect

class Seissol(SConsPackage):
    """FIXME: Put a proper description of your package here."""
 
    homepage = "http://www.seissol.org"
    #url      = "https://github.com/SeisSol/SeisSol/archive/201703.tar.gz"
    git = 'https://github.com/Seissol/SeisSol.git'

    version('ebeb324', commit='ebeb3247e675b925b065856e11e658585fffefd0',
            submodules=True, preferred=True)

    variant('numpy',default=True,
            description="numpy, (may be dropped if supplied by system python)")
    variant('scipy',default=True,
            description="scipy, (may be dropped if supplied by system python)")

    variant('netcdf', default=True,)
    variant('hdf5', default=True)
    variant('metis', default=True)
    variant('asagi', default=True)
    variant('memkind', default=True)

    variant('precision', default='d', values=('d','s'), multi=True)
    variant('cpu',default='noarch',
            values=('noarch','wsm', 'snb', 'knc', 'hsw', 'knl', 'skx',), multi=True)
    variant('order', default='4', values=('2','3','4','5','6','7','8'), multi=True)
    variant('mode', default='release', values=('release','debug',), multi=True)
    variant('mpi', default=True)
    variant('openmp', default=True)
    variant('logLevel', default='info',values=('info','debug',), multi=False)

    depends_on('py-numpy', when="+numpy")
    depends_on('py-scipy', when="+scipy")
    depends_on('netcdf +shared +mpi', when="+netcdf+mpi")
    depends_on('netcdf +shared ~mpi', when="+netcdf~mpi")
    depends_on('hdf5 +cxx +fortran +hl +shared +mpi', when="+hdf5+mpi")
    depends_on('hdf5 +cxx +fortran +hl +shared ~mpi', when="+hdf5~mpi")
    depends_on('libxsmm +generator')
    depends_on('metis +int64+shared', when='+metis')
    depends_on('parmetis +shared', when='+metis')
    depends_on('asagi', when='+asagi')
    depends_on('mpi', when='+mpi')
    depends_on('cmake')
    depends_on('memkind', when='+memkind')
    
    phases = ['edit','build', 'install']

    def edit(self, spec, prefix):
        
        filter_file("'-Wno-error=unknown-pragmas'","'-Wno-error=unknown-pragmas','-Wno-error=unused-variable','-Wno-error=narrowing'",'SConstruct')
        
    def build(self, spec, prefix):
        
        for mode in spec.variants['mode'].value:
            for cpu in spec.variants['cpu'].value:
                print('cpu:',cpu)
                for precision in spec.variants['precision'].value:
                    for order in spec.variants['order'].value:
                        args = self.build_args(spec, prefix)
                        args.append('order=' + order)
                        args.append('arch=' + precision + cpu)
                        args.append('compileMode=' + mode)
                        inspect.getmodule(self).scons(*args)
                        
    def build_args(self, spec, prefix):

        for k,v in spec.variants.__dict__.items():
            print(str(k)+str(v))
        args=[]
        args.append("logLevel=" + spec.variants['logLevel'].value)

        parallel = 'none'
        if '+mpi' in spec and '+openmp' in spec:
            parallel = 'hybrid'
        elif '+mpi' in spec and '~openmp' in spec:
            parallel = 'mpi'
        elif '~mpi' in spec and '+openmp' in spec:
            parallel = 'omp'

        args.append('parallelization=' + parallel)

        if spec.compiler.name in ['gcc' ,'intel']:
            args.append("compiler=" + spec.compiler.name)
        else:
            args.append("compiler=" + spec.compiler.name)
            print("seissol has not been tested for this compiler" +
                     str(spec.compiler.name) + 
                     "if possible use gnu or intel compilers")
            pass
        if '+netcdf' in spec:
            args.append("netcdf=yes")
            args.append("netcdfDir="+str(spec['netcdf'].prefix))
        if '+hdf5' in spec:
            args.append("hdf5=yes")
            args.append("hdf5Dir="+str(spec['hdf5'].prefix))
        if '+metis' in spec:
            args.append("metis=yes")
            args.append("metisDir="+str(spec['metis'].prefix))
        if '+memkind' in spec:
            args.append("memkindDir="+str(os.path.join(spec['memkind'].prefix)))

        return args

    def install(self,spec,prefix):
        install_tree('build',prefix.build)
        install_tree('Maple',prefix.Maple)
        install_tree('preprocessing',prefix.preprocessing)
        install_tree('postprocessing',prefix.postprocessing)
        install('README.md',prefix)
        mkdirp(prefix.bin)
        for file in os.listdir(prefix.build):
            if os.path.isfile(os.path.join(prefix.build,file)):
                if os.access(os.path.join(prefix.build,file),os.X_OK):
                    os.symlink(os.path.join('../build',file),os.path.join(prefix.bin,file))
