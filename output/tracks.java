// ORM class for table 'tracks'
// WARNING: This class is AUTO-GENERATED. Modify at your own risk.
//
// Debug information:
// Generated date: Thu Apr 16 16:30:04 MSK 2026
// For connector: org.apache.sqoop.manager.PostgresqlManager
import org.apache.hadoop.io.BytesWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.Writable;
import org.apache.hadoop.mapred.lib.db.DBWritable;
import org.apache.sqoop.lib.JdbcWritableBridge;
import org.apache.sqoop.lib.DelimiterSet;
import org.apache.sqoop.lib.FieldFormatter;
import org.apache.sqoop.lib.RecordParser;
import org.apache.sqoop.lib.BooleanParser;
import org.apache.sqoop.lib.BlobRef;
import org.apache.sqoop.lib.ClobRef;
import org.apache.sqoop.lib.LargeObjectLoader;
import org.apache.sqoop.lib.SqoopRecord;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.sql.Date;
import java.sql.Time;
import java.sql.Timestamp;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

public class tracks extends SqoopRecord  implements DBWritable, Writable {
  private final int PROTOCOL_VERSION = 3;
  public int getClassFormatVersion() { return PROTOCOL_VERSION; }
  public static interface FieldSetterCommand {    void setField(Object value);  }  protected ResultSet __cur_result_set;
  private Map<String, FieldSetterCommand> setters = new HashMap<String, FieldSetterCommand>();
  private void init0() {
    setters.put("id", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.id = (String)value;
      }
    });
    setters.put("name", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.name = (String)value;
      }
    });
    setters.put("album", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.album = (String)value;
      }
    });
    setters.put("album_id", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.album_id = (String)value;
      }
    });
    setters.put("artists", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.artists = (String)value;
      }
    });
    setters.put("artist_ids", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.artist_ids = (String)value;
      }
    });
    setters.put("track_number", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.track_number = (Integer)value;
      }
    });
    setters.put("disc_number", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.disc_number = (Integer)value;
      }
    });
    setters.put("explicit", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.explicit = (Boolean)value;
      }
    });
    setters.put("danceability", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.danceability = (Double)value;
      }
    });
    setters.put("energy", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.energy = (Double)value;
      }
    });
    setters.put("key", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.key = (Integer)value;
      }
    });
    setters.put("loudness", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.loudness = (Double)value;
      }
    });
    setters.put("mode", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.mode = (Integer)value;
      }
    });
    setters.put("speechiness", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.speechiness = (Double)value;
      }
    });
    setters.put("acousticness", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.acousticness = (Double)value;
      }
    });
    setters.put("instrumentalness", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.instrumentalness = (Double)value;
      }
    });
    setters.put("liveness", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.liveness = (Double)value;
      }
    });
    setters.put("valence", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.valence = (Double)value;
      }
    });
    setters.put("tempo", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.tempo = (Double)value;
      }
    });
    setters.put("duration_ms", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.duration_ms = (Integer)value;
      }
    });
    setters.put("time_signature", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.time_signature = (Double)value;
      }
    });
    setters.put("year", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.year = (Integer)value;
      }
    });
    setters.put("release_date", new FieldSetterCommand() {
      @Override
      public void setField(Object value) {
        tracks.this.release_date = (String)value;
      }
    });
  }
  public tracks() {
    init0();
  }
  private String id;
  public String get_id() {
    return id;
  }
  public void set_id(String id) {
    this.id = id;
  }
  public tracks with_id(String id) {
    this.id = id;
    return this;
  }
  private String name;
  public String get_name() {
    return name;
  }
  public void set_name(String name) {
    this.name = name;
  }
  public tracks with_name(String name) {
    this.name = name;
    return this;
  }
  private String album;
  public String get_album() {
    return album;
  }
  public void set_album(String album) {
    this.album = album;
  }
  public tracks with_album(String album) {
    this.album = album;
    return this;
  }
  private String album_id;
  public String get_album_id() {
    return album_id;
  }
  public void set_album_id(String album_id) {
    this.album_id = album_id;
  }
  public tracks with_album_id(String album_id) {
    this.album_id = album_id;
    return this;
  }
  private String artists;
  public String get_artists() {
    return artists;
  }
  public void set_artists(String artists) {
    this.artists = artists;
  }
  public tracks with_artists(String artists) {
    this.artists = artists;
    return this;
  }
  private String artist_ids;
  public String get_artist_ids() {
    return artist_ids;
  }
  public void set_artist_ids(String artist_ids) {
    this.artist_ids = artist_ids;
  }
  public tracks with_artist_ids(String artist_ids) {
    this.artist_ids = artist_ids;
    return this;
  }
  private Integer track_number;
  public Integer get_track_number() {
    return track_number;
  }
  public void set_track_number(Integer track_number) {
    this.track_number = track_number;
  }
  public tracks with_track_number(Integer track_number) {
    this.track_number = track_number;
    return this;
  }
  private Integer disc_number;
  public Integer get_disc_number() {
    return disc_number;
  }
  public void set_disc_number(Integer disc_number) {
    this.disc_number = disc_number;
  }
  public tracks with_disc_number(Integer disc_number) {
    this.disc_number = disc_number;
    return this;
  }
  private Boolean explicit;
  public Boolean get_explicit() {
    return explicit;
  }
  public void set_explicit(Boolean explicit) {
    this.explicit = explicit;
  }
  public tracks with_explicit(Boolean explicit) {
    this.explicit = explicit;
    return this;
  }
  private Double danceability;
  public Double get_danceability() {
    return danceability;
  }
  public void set_danceability(Double danceability) {
    this.danceability = danceability;
  }
  public tracks with_danceability(Double danceability) {
    this.danceability = danceability;
    return this;
  }
  private Double energy;
  public Double get_energy() {
    return energy;
  }
  public void set_energy(Double energy) {
    this.energy = energy;
  }
  public tracks with_energy(Double energy) {
    this.energy = energy;
    return this;
  }
  private Integer key;
  public Integer get_key() {
    return key;
  }
  public void set_key(Integer key) {
    this.key = key;
  }
  public tracks with_key(Integer key) {
    this.key = key;
    return this;
  }
  private Double loudness;
  public Double get_loudness() {
    return loudness;
  }
  public void set_loudness(Double loudness) {
    this.loudness = loudness;
  }
  public tracks with_loudness(Double loudness) {
    this.loudness = loudness;
    return this;
  }
  private Integer mode;
  public Integer get_mode() {
    return mode;
  }
  public void set_mode(Integer mode) {
    this.mode = mode;
  }
  public tracks with_mode(Integer mode) {
    this.mode = mode;
    return this;
  }
  private Double speechiness;
  public Double get_speechiness() {
    return speechiness;
  }
  public void set_speechiness(Double speechiness) {
    this.speechiness = speechiness;
  }
  public tracks with_speechiness(Double speechiness) {
    this.speechiness = speechiness;
    return this;
  }
  private Double acousticness;
  public Double get_acousticness() {
    return acousticness;
  }
  public void set_acousticness(Double acousticness) {
    this.acousticness = acousticness;
  }
  public tracks with_acousticness(Double acousticness) {
    this.acousticness = acousticness;
    return this;
  }
  private Double instrumentalness;
  public Double get_instrumentalness() {
    return instrumentalness;
  }
  public void set_instrumentalness(Double instrumentalness) {
    this.instrumentalness = instrumentalness;
  }
  public tracks with_instrumentalness(Double instrumentalness) {
    this.instrumentalness = instrumentalness;
    return this;
  }
  private Double liveness;
  public Double get_liveness() {
    return liveness;
  }
  public void set_liveness(Double liveness) {
    this.liveness = liveness;
  }
  public tracks with_liveness(Double liveness) {
    this.liveness = liveness;
    return this;
  }
  private Double valence;
  public Double get_valence() {
    return valence;
  }
  public void set_valence(Double valence) {
    this.valence = valence;
  }
  public tracks with_valence(Double valence) {
    this.valence = valence;
    return this;
  }
  private Double tempo;
  public Double get_tempo() {
    return tempo;
  }
  public void set_tempo(Double tempo) {
    this.tempo = tempo;
  }
  public tracks with_tempo(Double tempo) {
    this.tempo = tempo;
    return this;
  }
  private Integer duration_ms;
  public Integer get_duration_ms() {
    return duration_ms;
  }
  public void set_duration_ms(Integer duration_ms) {
    this.duration_ms = duration_ms;
  }
  public tracks with_duration_ms(Integer duration_ms) {
    this.duration_ms = duration_ms;
    return this;
  }
  private Double time_signature;
  public Double get_time_signature() {
    return time_signature;
  }
  public void set_time_signature(Double time_signature) {
    this.time_signature = time_signature;
  }
  public tracks with_time_signature(Double time_signature) {
    this.time_signature = time_signature;
    return this;
  }
  private Integer year;
  public Integer get_year() {
    return year;
  }
  public void set_year(Integer year) {
    this.year = year;
  }
  public tracks with_year(Integer year) {
    this.year = year;
    return this;
  }
  private String release_date;
  public String get_release_date() {
    return release_date;
  }
  public void set_release_date(String release_date) {
    this.release_date = release_date;
  }
  public tracks with_release_date(String release_date) {
    this.release_date = release_date;
    return this;
  }
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (!(o instanceof tracks)) {
      return false;
    }
    tracks that = (tracks) o;
    boolean equal = true;
    equal = equal && (this.id == null ? that.id == null : this.id.equals(that.id));
    equal = equal && (this.name == null ? that.name == null : this.name.equals(that.name));
    equal = equal && (this.album == null ? that.album == null : this.album.equals(that.album));
    equal = equal && (this.album_id == null ? that.album_id == null : this.album_id.equals(that.album_id));
    equal = equal && (this.artists == null ? that.artists == null : this.artists.equals(that.artists));
    equal = equal && (this.artist_ids == null ? that.artist_ids == null : this.artist_ids.equals(that.artist_ids));
    equal = equal && (this.track_number == null ? that.track_number == null : this.track_number.equals(that.track_number));
    equal = equal && (this.disc_number == null ? that.disc_number == null : this.disc_number.equals(that.disc_number));
    equal = equal && (this.explicit == null ? that.explicit == null : this.explicit.equals(that.explicit));
    equal = equal && (this.danceability == null ? that.danceability == null : this.danceability.equals(that.danceability));
    equal = equal && (this.energy == null ? that.energy == null : this.energy.equals(that.energy));
    equal = equal && (this.key == null ? that.key == null : this.key.equals(that.key));
    equal = equal && (this.loudness == null ? that.loudness == null : this.loudness.equals(that.loudness));
    equal = equal && (this.mode == null ? that.mode == null : this.mode.equals(that.mode));
    equal = equal && (this.speechiness == null ? that.speechiness == null : this.speechiness.equals(that.speechiness));
    equal = equal && (this.acousticness == null ? that.acousticness == null : this.acousticness.equals(that.acousticness));
    equal = equal && (this.instrumentalness == null ? that.instrumentalness == null : this.instrumentalness.equals(that.instrumentalness));
    equal = equal && (this.liveness == null ? that.liveness == null : this.liveness.equals(that.liveness));
    equal = equal && (this.valence == null ? that.valence == null : this.valence.equals(that.valence));
    equal = equal && (this.tempo == null ? that.tempo == null : this.tempo.equals(that.tempo));
    equal = equal && (this.duration_ms == null ? that.duration_ms == null : this.duration_ms.equals(that.duration_ms));
    equal = equal && (this.time_signature == null ? that.time_signature == null : this.time_signature.equals(that.time_signature));
    equal = equal && (this.year == null ? that.year == null : this.year.equals(that.year));
    equal = equal && (this.release_date == null ? that.release_date == null : this.release_date.equals(that.release_date));
    return equal;
  }
  public boolean equals0(Object o) {
    if (this == o) {
      return true;
    }
    if (!(o instanceof tracks)) {
      return false;
    }
    tracks that = (tracks) o;
    boolean equal = true;
    equal = equal && (this.id == null ? that.id == null : this.id.equals(that.id));
    equal = equal && (this.name == null ? that.name == null : this.name.equals(that.name));
    equal = equal && (this.album == null ? that.album == null : this.album.equals(that.album));
    equal = equal && (this.album_id == null ? that.album_id == null : this.album_id.equals(that.album_id));
    equal = equal && (this.artists == null ? that.artists == null : this.artists.equals(that.artists));
    equal = equal && (this.artist_ids == null ? that.artist_ids == null : this.artist_ids.equals(that.artist_ids));
    equal = equal && (this.track_number == null ? that.track_number == null : this.track_number.equals(that.track_number));
    equal = equal && (this.disc_number == null ? that.disc_number == null : this.disc_number.equals(that.disc_number));
    equal = equal && (this.explicit == null ? that.explicit == null : this.explicit.equals(that.explicit));
    equal = equal && (this.danceability == null ? that.danceability == null : this.danceability.equals(that.danceability));
    equal = equal && (this.energy == null ? that.energy == null : this.energy.equals(that.energy));
    equal = equal && (this.key == null ? that.key == null : this.key.equals(that.key));
    equal = equal && (this.loudness == null ? that.loudness == null : this.loudness.equals(that.loudness));
    equal = equal && (this.mode == null ? that.mode == null : this.mode.equals(that.mode));
    equal = equal && (this.speechiness == null ? that.speechiness == null : this.speechiness.equals(that.speechiness));
    equal = equal && (this.acousticness == null ? that.acousticness == null : this.acousticness.equals(that.acousticness));
    equal = equal && (this.instrumentalness == null ? that.instrumentalness == null : this.instrumentalness.equals(that.instrumentalness));
    equal = equal && (this.liveness == null ? that.liveness == null : this.liveness.equals(that.liveness));
    equal = equal && (this.valence == null ? that.valence == null : this.valence.equals(that.valence));
    equal = equal && (this.tempo == null ? that.tempo == null : this.tempo.equals(that.tempo));
    equal = equal && (this.duration_ms == null ? that.duration_ms == null : this.duration_ms.equals(that.duration_ms));
    equal = equal && (this.time_signature == null ? that.time_signature == null : this.time_signature.equals(that.time_signature));
    equal = equal && (this.year == null ? that.year == null : this.year.equals(that.year));
    equal = equal && (this.release_date == null ? that.release_date == null : this.release_date.equals(that.release_date));
    return equal;
  }
  public void readFields(ResultSet __dbResults) throws SQLException {
    this.__cur_result_set = __dbResults;
    this.id = JdbcWritableBridge.readString(1, __dbResults);
    this.name = JdbcWritableBridge.readString(2, __dbResults);
    this.album = JdbcWritableBridge.readString(3, __dbResults);
    this.album_id = JdbcWritableBridge.readString(4, __dbResults);
    this.artists = JdbcWritableBridge.readString(5, __dbResults);
    this.artist_ids = JdbcWritableBridge.readString(6, __dbResults);
    this.track_number = JdbcWritableBridge.readInteger(7, __dbResults);
    this.disc_number = JdbcWritableBridge.readInteger(8, __dbResults);
    this.explicit = JdbcWritableBridge.readBoolean(9, __dbResults);
    this.danceability = JdbcWritableBridge.readDouble(10, __dbResults);
    this.energy = JdbcWritableBridge.readDouble(11, __dbResults);
    this.key = JdbcWritableBridge.readInteger(12, __dbResults);
    this.loudness = JdbcWritableBridge.readDouble(13, __dbResults);
    this.mode = JdbcWritableBridge.readInteger(14, __dbResults);
    this.speechiness = JdbcWritableBridge.readDouble(15, __dbResults);
    this.acousticness = JdbcWritableBridge.readDouble(16, __dbResults);
    this.instrumentalness = JdbcWritableBridge.readDouble(17, __dbResults);
    this.liveness = JdbcWritableBridge.readDouble(18, __dbResults);
    this.valence = JdbcWritableBridge.readDouble(19, __dbResults);
    this.tempo = JdbcWritableBridge.readDouble(20, __dbResults);
    this.duration_ms = JdbcWritableBridge.readInteger(21, __dbResults);
    this.time_signature = JdbcWritableBridge.readDouble(22, __dbResults);
    this.year = JdbcWritableBridge.readInteger(23, __dbResults);
    this.release_date = JdbcWritableBridge.readString(24, __dbResults);
  }
  public void readFields0(ResultSet __dbResults) throws SQLException {
    this.id = JdbcWritableBridge.readString(1, __dbResults);
    this.name = JdbcWritableBridge.readString(2, __dbResults);
    this.album = JdbcWritableBridge.readString(3, __dbResults);
    this.album_id = JdbcWritableBridge.readString(4, __dbResults);
    this.artists = JdbcWritableBridge.readString(5, __dbResults);
    this.artist_ids = JdbcWritableBridge.readString(6, __dbResults);
    this.track_number = JdbcWritableBridge.readInteger(7, __dbResults);
    this.disc_number = JdbcWritableBridge.readInteger(8, __dbResults);
    this.explicit = JdbcWritableBridge.readBoolean(9, __dbResults);
    this.danceability = JdbcWritableBridge.readDouble(10, __dbResults);
    this.energy = JdbcWritableBridge.readDouble(11, __dbResults);
    this.key = JdbcWritableBridge.readInteger(12, __dbResults);
    this.loudness = JdbcWritableBridge.readDouble(13, __dbResults);
    this.mode = JdbcWritableBridge.readInteger(14, __dbResults);
    this.speechiness = JdbcWritableBridge.readDouble(15, __dbResults);
    this.acousticness = JdbcWritableBridge.readDouble(16, __dbResults);
    this.instrumentalness = JdbcWritableBridge.readDouble(17, __dbResults);
    this.liveness = JdbcWritableBridge.readDouble(18, __dbResults);
    this.valence = JdbcWritableBridge.readDouble(19, __dbResults);
    this.tempo = JdbcWritableBridge.readDouble(20, __dbResults);
    this.duration_ms = JdbcWritableBridge.readInteger(21, __dbResults);
    this.time_signature = JdbcWritableBridge.readDouble(22, __dbResults);
    this.year = JdbcWritableBridge.readInteger(23, __dbResults);
    this.release_date = JdbcWritableBridge.readString(24, __dbResults);
  }
  public void loadLargeObjects(LargeObjectLoader __loader)
      throws SQLException, IOException, InterruptedException {
  }
  public void loadLargeObjects0(LargeObjectLoader __loader)
      throws SQLException, IOException, InterruptedException {
  }
  public void write(PreparedStatement __dbStmt) throws SQLException {
    write(__dbStmt, 0);
  }

  public int write(PreparedStatement __dbStmt, int __off) throws SQLException {
    JdbcWritableBridge.writeString(id, 1 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(name, 2 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(album, 3 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(album_id, 4 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(artists, 5 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(artist_ids, 6 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeInteger(track_number, 7 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeInteger(disc_number, 8 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeBoolean(explicit, 9 + __off, -7, __dbStmt);
    JdbcWritableBridge.writeDouble(danceability, 10 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(energy, 11 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(key, 12 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(loudness, 13 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(mode, 14 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(speechiness, 15 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(acousticness, 16 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(instrumentalness, 17 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(liveness, 18 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(valence, 19 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(tempo, 20 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(duration_ms, 21 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(time_signature, 22 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(year, 23 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeString(release_date, 24 + __off, 12, __dbStmt);
    return 24;
  }
  public void write0(PreparedStatement __dbStmt, int __off) throws SQLException {
    JdbcWritableBridge.writeString(id, 1 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(name, 2 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(album, 3 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(album_id, 4 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(artists, 5 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeString(artist_ids, 6 + __off, 12, __dbStmt);
    JdbcWritableBridge.writeInteger(track_number, 7 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeInteger(disc_number, 8 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeBoolean(explicit, 9 + __off, -7, __dbStmt);
    JdbcWritableBridge.writeDouble(danceability, 10 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(energy, 11 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(key, 12 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(loudness, 13 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(mode, 14 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(speechiness, 15 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(acousticness, 16 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(instrumentalness, 17 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(liveness, 18 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(valence, 19 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeDouble(tempo, 20 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(duration_ms, 21 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeDouble(time_signature, 22 + __off, 8, __dbStmt);
    JdbcWritableBridge.writeInteger(year, 23 + __off, 4, __dbStmt);
    JdbcWritableBridge.writeString(release_date, 24 + __off, 12, __dbStmt);
  }
  public void readFields(DataInput __dataIn) throws IOException {
this.readFields0(__dataIn);  }
  public void readFields0(DataInput __dataIn) throws IOException {
    if (__dataIn.readBoolean()) { 
        this.id = null;
    } else {
    this.id = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.name = null;
    } else {
    this.name = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.album = null;
    } else {
    this.album = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.album_id = null;
    } else {
    this.album_id = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.artists = null;
    } else {
    this.artists = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.artist_ids = null;
    } else {
    this.artist_ids = Text.readString(__dataIn);
    }
    if (__dataIn.readBoolean()) { 
        this.track_number = null;
    } else {
    this.track_number = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.disc_number = null;
    } else {
    this.disc_number = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.explicit = null;
    } else {
    this.explicit = Boolean.valueOf(__dataIn.readBoolean());
    }
    if (__dataIn.readBoolean()) { 
        this.danceability = null;
    } else {
    this.danceability = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.energy = null;
    } else {
    this.energy = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.key = null;
    } else {
    this.key = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.loudness = null;
    } else {
    this.loudness = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.mode = null;
    } else {
    this.mode = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.speechiness = null;
    } else {
    this.speechiness = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.acousticness = null;
    } else {
    this.acousticness = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.instrumentalness = null;
    } else {
    this.instrumentalness = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.liveness = null;
    } else {
    this.liveness = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.valence = null;
    } else {
    this.valence = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.tempo = null;
    } else {
    this.tempo = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.duration_ms = null;
    } else {
    this.duration_ms = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.time_signature = null;
    } else {
    this.time_signature = Double.valueOf(__dataIn.readDouble());
    }
    if (__dataIn.readBoolean()) { 
        this.year = null;
    } else {
    this.year = Integer.valueOf(__dataIn.readInt());
    }
    if (__dataIn.readBoolean()) { 
        this.release_date = null;
    } else {
    this.release_date = Text.readString(__dataIn);
    }
  }
  public void write(DataOutput __dataOut) throws IOException {
    if (null == this.id) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, id);
    }
    if (null == this.name) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, name);
    }
    if (null == this.album) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, album);
    }
    if (null == this.album_id) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, album_id);
    }
    if (null == this.artists) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, artists);
    }
    if (null == this.artist_ids) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, artist_ids);
    }
    if (null == this.track_number) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.track_number);
    }
    if (null == this.disc_number) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.disc_number);
    }
    if (null == this.explicit) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeBoolean(this.explicit);
    }
    if (null == this.danceability) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.danceability);
    }
    if (null == this.energy) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.energy);
    }
    if (null == this.key) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.key);
    }
    if (null == this.loudness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.loudness);
    }
    if (null == this.mode) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.mode);
    }
    if (null == this.speechiness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.speechiness);
    }
    if (null == this.acousticness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.acousticness);
    }
    if (null == this.instrumentalness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.instrumentalness);
    }
    if (null == this.liveness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.liveness);
    }
    if (null == this.valence) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.valence);
    }
    if (null == this.tempo) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.tempo);
    }
    if (null == this.duration_ms) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.duration_ms);
    }
    if (null == this.time_signature) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.time_signature);
    }
    if (null == this.year) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.year);
    }
    if (null == this.release_date) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, release_date);
    }
  }
  public void write0(DataOutput __dataOut) throws IOException {
    if (null == this.id) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, id);
    }
    if (null == this.name) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, name);
    }
    if (null == this.album) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, album);
    }
    if (null == this.album_id) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, album_id);
    }
    if (null == this.artists) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, artists);
    }
    if (null == this.artist_ids) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, artist_ids);
    }
    if (null == this.track_number) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.track_number);
    }
    if (null == this.disc_number) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.disc_number);
    }
    if (null == this.explicit) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeBoolean(this.explicit);
    }
    if (null == this.danceability) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.danceability);
    }
    if (null == this.energy) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.energy);
    }
    if (null == this.key) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.key);
    }
    if (null == this.loudness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.loudness);
    }
    if (null == this.mode) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.mode);
    }
    if (null == this.speechiness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.speechiness);
    }
    if (null == this.acousticness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.acousticness);
    }
    if (null == this.instrumentalness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.instrumentalness);
    }
    if (null == this.liveness) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.liveness);
    }
    if (null == this.valence) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.valence);
    }
    if (null == this.tempo) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.tempo);
    }
    if (null == this.duration_ms) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.duration_ms);
    }
    if (null == this.time_signature) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeDouble(this.time_signature);
    }
    if (null == this.year) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    __dataOut.writeInt(this.year);
    }
    if (null == this.release_date) { 
        __dataOut.writeBoolean(true);
    } else {
        __dataOut.writeBoolean(false);
    Text.writeString(__dataOut, release_date);
    }
  }
  private static final DelimiterSet __outputDelimiters = new DelimiterSet((char) 44, (char) 10, (char) 0, (char) 0, false);
  public String toString() {
    return toString(__outputDelimiters, true);
  }
  public String toString(DelimiterSet delimiters) {
    return toString(delimiters, true);
  }
  public String toString(boolean useRecordDelim) {
    return toString(__outputDelimiters, useRecordDelim);
  }
  public String toString(DelimiterSet delimiters, boolean useRecordDelim) {
    StringBuilder __sb = new StringBuilder();
    char fieldDelim = delimiters.getFieldsTerminatedBy();
    __sb.append(FieldFormatter.escapeAndEnclose(id==null?"null":id, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(name==null?"null":name, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(album==null?"null":album, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(album_id==null?"null":album_id, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(artists==null?"null":artists, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(artist_ids==null?"null":artist_ids, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(track_number==null?"null":"" + track_number, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(disc_number==null?"null":"" + disc_number, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(explicit==null?"null":"" + explicit, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(danceability==null?"null":"" + danceability, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(energy==null?"null":"" + energy, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(key==null?"null":"" + key, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(loudness==null?"null":"" + loudness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(mode==null?"null":"" + mode, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(speechiness==null?"null":"" + speechiness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(acousticness==null?"null":"" + acousticness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(instrumentalness==null?"null":"" + instrumentalness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(liveness==null?"null":"" + liveness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(valence==null?"null":"" + valence, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(tempo==null?"null":"" + tempo, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(duration_ms==null?"null":"" + duration_ms, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(time_signature==null?"null":"" + time_signature, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(year==null?"null":"" + year, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(release_date==null?"null":release_date, delimiters));
    if (useRecordDelim) {
      __sb.append(delimiters.getLinesTerminatedBy());
    }
    return __sb.toString();
  }
  public void toString0(DelimiterSet delimiters, StringBuilder __sb, char fieldDelim) {
    __sb.append(FieldFormatter.escapeAndEnclose(id==null?"null":id, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(name==null?"null":name, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(album==null?"null":album, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(album_id==null?"null":album_id, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(artists==null?"null":artists, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(artist_ids==null?"null":artist_ids, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(track_number==null?"null":"" + track_number, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(disc_number==null?"null":"" + disc_number, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(explicit==null?"null":"" + explicit, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(danceability==null?"null":"" + danceability, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(energy==null?"null":"" + energy, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(key==null?"null":"" + key, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(loudness==null?"null":"" + loudness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(mode==null?"null":"" + mode, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(speechiness==null?"null":"" + speechiness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(acousticness==null?"null":"" + acousticness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(instrumentalness==null?"null":"" + instrumentalness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(liveness==null?"null":"" + liveness, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(valence==null?"null":"" + valence, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(tempo==null?"null":"" + tempo, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(duration_ms==null?"null":"" + duration_ms, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(time_signature==null?"null":"" + time_signature, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(year==null?"null":"" + year, delimiters));
    __sb.append(fieldDelim);
    __sb.append(FieldFormatter.escapeAndEnclose(release_date==null?"null":release_date, delimiters));
  }
  private static final DelimiterSet __inputDelimiters = new DelimiterSet((char) 44, (char) 10, (char) 0, (char) 0, false);
  private RecordParser __parser;
  public void parse(Text __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  public void parse(CharSequence __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  public void parse(byte [] __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  public void parse(char [] __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  public void parse(ByteBuffer __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  public void parse(CharBuffer __record) throws RecordParser.ParseError {
    if (null == this.__parser) {
      this.__parser = new RecordParser(__inputDelimiters);
    }
    List<String> __fields = this.__parser.parseRecord(__record);
    __loadFromFields(__fields);
  }

  private void __loadFromFields(List<String> fields) {
    Iterator<String> __it = fields.listIterator();
    String __cur_str = null;
    try {
    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.id = null; } else {
      this.id = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.name = null; } else {
      this.name = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.album = null; } else {
      this.album = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.album_id = null; } else {
      this.album_id = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.artists = null; } else {
      this.artists = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.artist_ids = null; } else {
      this.artist_ids = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.track_number = null; } else {
      this.track_number = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.disc_number = null; } else {
      this.disc_number = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.explicit = null; } else {
      this.explicit = BooleanParser.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.danceability = null; } else {
      this.danceability = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.energy = null; } else {
      this.energy = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.key = null; } else {
      this.key = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.loudness = null; } else {
      this.loudness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.mode = null; } else {
      this.mode = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.speechiness = null; } else {
      this.speechiness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.acousticness = null; } else {
      this.acousticness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.instrumentalness = null; } else {
      this.instrumentalness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.liveness = null; } else {
      this.liveness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.valence = null; } else {
      this.valence = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.tempo = null; } else {
      this.tempo = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.duration_ms = null; } else {
      this.duration_ms = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.time_signature = null; } else {
      this.time_signature = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.year = null; } else {
      this.year = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.release_date = null; } else {
      this.release_date = __cur_str;
    }

    } catch (RuntimeException e) {    throw new RuntimeException("Can't parse input data: '" + __cur_str + "'", e);    }  }

  private void __loadFromFields0(Iterator<String> __it) {
    String __cur_str = null;
    try {
    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.id = null; } else {
      this.id = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.name = null; } else {
      this.name = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.album = null; } else {
      this.album = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.album_id = null; } else {
      this.album_id = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.artists = null; } else {
      this.artists = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.artist_ids = null; } else {
      this.artist_ids = __cur_str;
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.track_number = null; } else {
      this.track_number = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.disc_number = null; } else {
      this.disc_number = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.explicit = null; } else {
      this.explicit = BooleanParser.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.danceability = null; } else {
      this.danceability = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.energy = null; } else {
      this.energy = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.key = null; } else {
      this.key = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.loudness = null; } else {
      this.loudness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.mode = null; } else {
      this.mode = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.speechiness = null; } else {
      this.speechiness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.acousticness = null; } else {
      this.acousticness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.instrumentalness = null; } else {
      this.instrumentalness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.liveness = null; } else {
      this.liveness = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.valence = null; } else {
      this.valence = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.tempo = null; } else {
      this.tempo = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.duration_ms = null; } else {
      this.duration_ms = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.time_signature = null; } else {
      this.time_signature = Double.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null") || __cur_str.length() == 0) { this.year = null; } else {
      this.year = Integer.valueOf(__cur_str);
    }

    if (__it.hasNext()) {
        __cur_str = __it.next();
    } else {
        __cur_str = "null";
    }
    if (__cur_str.equals("null")) { this.release_date = null; } else {
      this.release_date = __cur_str;
    }

    } catch (RuntimeException e) {    throw new RuntimeException("Can't parse input data: '" + __cur_str + "'", e);    }  }

  public Object clone() throws CloneNotSupportedException {
    tracks o = (tracks) super.clone();
    return o;
  }

  public void clone0(tracks o) throws CloneNotSupportedException {
  }

  public Map<String, Object> getFieldMap() {
    Map<String, Object> __sqoop$field_map = new HashMap<String, Object>();
    __sqoop$field_map.put("id", this.id);
    __sqoop$field_map.put("name", this.name);
    __sqoop$field_map.put("album", this.album);
    __sqoop$field_map.put("album_id", this.album_id);
    __sqoop$field_map.put("artists", this.artists);
    __sqoop$field_map.put("artist_ids", this.artist_ids);
    __sqoop$field_map.put("track_number", this.track_number);
    __sqoop$field_map.put("disc_number", this.disc_number);
    __sqoop$field_map.put("explicit", this.explicit);
    __sqoop$field_map.put("danceability", this.danceability);
    __sqoop$field_map.put("energy", this.energy);
    __sqoop$field_map.put("key", this.key);
    __sqoop$field_map.put("loudness", this.loudness);
    __sqoop$field_map.put("mode", this.mode);
    __sqoop$field_map.put("speechiness", this.speechiness);
    __sqoop$field_map.put("acousticness", this.acousticness);
    __sqoop$field_map.put("instrumentalness", this.instrumentalness);
    __sqoop$field_map.put("liveness", this.liveness);
    __sqoop$field_map.put("valence", this.valence);
    __sqoop$field_map.put("tempo", this.tempo);
    __sqoop$field_map.put("duration_ms", this.duration_ms);
    __sqoop$field_map.put("time_signature", this.time_signature);
    __sqoop$field_map.put("year", this.year);
    __sqoop$field_map.put("release_date", this.release_date);
    return __sqoop$field_map;
  }

  public void getFieldMap0(Map<String, Object> __sqoop$field_map) {
    __sqoop$field_map.put("id", this.id);
    __sqoop$field_map.put("name", this.name);
    __sqoop$field_map.put("album", this.album);
    __sqoop$field_map.put("album_id", this.album_id);
    __sqoop$field_map.put("artists", this.artists);
    __sqoop$field_map.put("artist_ids", this.artist_ids);
    __sqoop$field_map.put("track_number", this.track_number);
    __sqoop$field_map.put("disc_number", this.disc_number);
    __sqoop$field_map.put("explicit", this.explicit);
    __sqoop$field_map.put("danceability", this.danceability);
    __sqoop$field_map.put("energy", this.energy);
    __sqoop$field_map.put("key", this.key);
    __sqoop$field_map.put("loudness", this.loudness);
    __sqoop$field_map.put("mode", this.mode);
    __sqoop$field_map.put("speechiness", this.speechiness);
    __sqoop$field_map.put("acousticness", this.acousticness);
    __sqoop$field_map.put("instrumentalness", this.instrumentalness);
    __sqoop$field_map.put("liveness", this.liveness);
    __sqoop$field_map.put("valence", this.valence);
    __sqoop$field_map.put("tempo", this.tempo);
    __sqoop$field_map.put("duration_ms", this.duration_ms);
    __sqoop$field_map.put("time_signature", this.time_signature);
    __sqoop$field_map.put("year", this.year);
    __sqoop$field_map.put("release_date", this.release_date);
  }

  public void setField(String __fieldName, Object __fieldVal) {
    if (!setters.containsKey(__fieldName)) {
      throw new RuntimeException("No such field:"+__fieldName);
    }
    setters.get(__fieldName).setField(__fieldVal);
  }

}
