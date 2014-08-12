import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectStreamClass;
import java.io.IOException;

// see http://sourceforge.net/tracker/index.php?func=detail&aid=1799807&group_id=109824&atid=655012
public class JPypeObjectInputStream extends ObjectInputStream
{
	public JPypeObjectInputStream(InputStream in) throws IOException
	{
		super(in);
	}

	protected Class<?> resolveClass(ObjectStreamClass desc) throws
		IOException, ClassNotFoundException
	{
		return Class.forName(desc.getName(), true,
							 ClassLoader.getSystemClassLoader());
	}
}
