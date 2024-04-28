from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from provider.db import Base
from sqlalchemy.orm import relationship

class user_activity(Base):
    __tablename__ = 'user_activity'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    no_hp = Column(String, unique=True)
    activity = Column(String)

    registrasi = relationship('registrasi', back_populates='user_activity')

class registrasi(Base):
    __tablename__ = 'registrasi'

    id_registrasi = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_user_activity = Column(Integer, ForeignKey('user_activity.id'))
    user_activity = relationship('user_activity', back_populates='registrasi')
    
    # data diri
    nama = Column(String)
    nik = Column(String)
    ttl = Column(String)
    jenis_kelamin = Column(String)
    no_hp = Column(String)
    member = Column(String)
    
    # alamat anggota
    provinsi = Column(String)
    kecamatan = Column(String)
    kabupaten_kota = Column(String)
    kode_pos = Column(String)
    warganegara = Column(String)
    alamat = Column(String)

    # jenis usaha
    jenis_usaha = Column(String)
    kelas_usaha = Column(String)
    deskripsi_usaha = Column(String)
    ijin_usaha = Column(String)